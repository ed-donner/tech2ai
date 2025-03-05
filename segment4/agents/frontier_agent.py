# imports

import os
import re
import math
import json
from typing import List, Dict
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from datasets import load_dataset
import chromadb
from items import Item
from testing import Tester
from agents.agent import Agent
from groq import Groq


class FrontierAgent(Agent):

    name = "Frontier Agent"
    color = Agent.BLUE

    MODEL_GPT = "gpt-4o-mini"
    MODEL_DEEPSEEK = "deepseek-r1-distill-llama-70b"
    PREPROCESS_MODEL = "llama3.2"
    
    def __init__(self, collection):
        """
        Set up this instance by connecting to OpenAI, to the Chroma Datastore,
        And setting up the vector encoding model
        """
        self.log("Initializing Frontier Agent")
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.client = Groq()
            self.MODEL = self.MODEL_DEEPSEEK
            self.log("Frontier Agent is set up with DeepSeek-R1 via Groq")
        else:
            self.client = OpenAI()
            self.MODEL = self.MODEL_GPT
            self.log("Frontier Agent is setting up with OpenAI")
        self.ollama_via_openai = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
        self.collection = collection
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
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

    def messages_for(self, description: str, similars: List[str], prices: List[float]) -> List[Dict[str, str]]:
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
            {"role": "assistant", "content": "Price is $"}
        ]

    def preprocess(self, item: str):
        """
        Run the description through llama3.2 running locally to make it most suitable for RAG lookup
        """
        system_message = "You rewrite product descriptions in a format most suitable for finding similar products in a Knowledge Base"
        user_message = "Please write a short 2-3 sentence description of the following product; your description will be used to find similar products so it should be comprehensive and only about the product. Details:\n"
        user_message += item
        user_message += "\n\nNow please reply only with the short description, with no introduction"
        messages = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
        response = self.ollama_via_openai.chat.completions.create(model=self.PREPROCESS_MODEL, messages=messages, seed=42)
        return response.choices[0].message.content

    def find_similars(self, description: str):
        """
        Return a list of items similar to the given one by looking in the Chroma datastore
        """
        self.log("Frontier Agent is using Llama 3.2 to preprocess the description")
        preprocessed = self.preprocess(description)
        self.log("Frontier Agent is vectorizing using all-MiniLM-L6-v2")
        vector = self.model.encode([preprocessed])
        self.log("Frontier Agent is performing a RAG search of the Chroma datastore to find 5 similar products")
        results = self.collection.query(query_embeddings=vector.astype(float).tolist(), n_results=5)
        documents = results['documents'][0][:]
        prices = [m['price'] for m in results['metadatas'][0][:]]
        self.log("Frontier Agent has found similar products")
        return documents, prices

    def get_price(self, s) -> float:
        """
        A utility that plucks a floating point number out of a string
        """
        s = s.replace('$','').replace(',','')
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else 0.0

    def price(self, description: str) -> float:
        """
        Make a call to OpenAI to estimate the price of the described product,
        by looking up 5 similar products and including them in the prompt to give context
        :param description: a description of the product
        :return: an estimate of the price
        """
        documents, prices = self.find_similars(description)
        self.log(f"Frontier Agent is about to call {self.MODEL} with RAG context of 5 similar products")
        messages = self.messages_for(description, documents, prices)
        if 'deepseek' in self.MODEL:
            messages[1]["content"] += "\nYou only need to guess the price, using the similar items to give you some reference point. Reply only with the price. Only think briefly; avoid overthinking."
        response = self.client.chat.completions.create(
            model=self.MODEL, 
            messages=self.messages_for(description, documents, prices),
            seed=42,
            max_tokens=5
        )
        reply = response.choices[0].message.content
        result = self.get_price(reply)
        self.log(f"Frontier Agent completed - predicting ${result:.2f}")
        return result
        