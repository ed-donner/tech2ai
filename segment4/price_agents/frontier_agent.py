import os
import re
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from price_agents.agent import Agent
from litellm import completion


class FrontierAgent(Agent):
    name = "Frontier Agent"
    color = Agent.YELLOW

    MODEL = "gemini/gemini-3-flash"
    PREPROCESS_MODEL = "groq/openai/gpt-oss-20b"

    def __init__(self, collection):
        """
        Set up this instance by connecting to OpenAI, to the Chroma Datastore,
        And setting up the vector encoding model
        """
        self.log("Initializing Frontier Agent")
        gemini_key = os.getenv("GOOGLE_API_KEY")
        if gemini_key:
            self.MODEL = "gemini/gemini-3-flash"
            self.log("Frontier Agent is set up with Gemini")
        else:
            self.MODEL = "gpt-4.1-mini"
            self.log("Frontier Agent is setting up with OpenAI")
        self.collection = collection
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.log("Frontier Agent is ready")

    def make_context(self, similars: List[str], prices: List[float]) -> str:
        """
        Create context that can be inserted into the prompt
        :param similars: similar products to the one being estimated
        :param prices: prices of the similar products
        :return: text to insert in the prompt that provides context
        """
        message = "To provide some context, here are some other items that might be similar to the item you need to estimate.\n\n"
        for similar, price in zip(similars, prices):
            message += f"Potentially related product:\n{similar}\nPrice is ${price:.2f}\n\n"
        return message

    def messages_for(
        self, description: str, similars: List[str], prices: List[float]
    ) -> List[Dict[str, str]]:
        """
        Create the message list to be included in a call to OpenAI
        With the system and user prompt
        :param description: a description of the product
        :param similars: similar products to this one
        :param prices: prices of similar products
        :return: the list of messages in the format expected by OpenAI
        """
        system_message = "You estimate prices of items. Reply only with the price, no explanation"
        user_prompt = self.make_context(similars, prices)
        user_prompt += "And now the question for you:\n\n"
        user_prompt += "How much does this cost?\n\n" + description
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": "Price is $"},
        ]

    def preprocess(self, item: str):
        """
        Run the description through groq running locally to make it most suitable for RAG lookup
        """
        message = f"Reply with a 2-3 sentence summary of this product. This will be used to find similar products so it should be clear, concise, complete. Details:\n{item}"
        messages = [{"role": "user", "content": message}]
        response = completion(model=self.PREPROCESS_MODEL, messages=messages)
        return response.choices[0].message.content

    def find_similars(self, description: str):
        """
        Return a list of items similar to the given one by looking in the Chroma datastore
        """
        self.log(f"Frontier Agent is preprocessing with {self.PREPROCESS_MODEL}")
        preprocessed = self.preprocess(description)
        self.log("Frontier Agent is vectorizing using all-MiniLM-L6-v2")
        vector = self.model.encode([preprocessed])
        self.log("Frontier Agent is performing a RAG search of Chroma to find similar products")
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results["documents"][0][:]
        prices = [m["price"] for m in results["metadatas"][0][:]]
        self.log("Frontier Agent has found similar products")
        return documents, prices

    def get_price(self, s) -> float:
        """
        A utility that plucks a floating point number out of a string
        """
        s = s.replace("$", "").replace(",", "")
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Make a call to OpenAI or DeepSeek to estimate the price of the described product,
        by looking up 5 similar products and including them in the prompt to give context
        :param description: a description of the product
        :return: an estimate of the price
        """
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent is calling {self.MODEL} with 5 similar products")
        messages = self.messages_for(description, documents, prices)
        response = completion(model=self.MODEL, messages=messages, max_tokens=8)
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed - predicting ${result:.2f}")
        return result
