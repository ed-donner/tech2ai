import os
from price_agents.deals import Opportunity
import requests
from price_agents.agent import Agent
from anthropic import Anthropic


class MessagingAgent(Agent):

    name = "Messaging Agent"
    color = Agent.MAGENTA
    MODEL = "claude-3-7-sonnet-latest"
    pushover_url = "https://api.pushover.net/1/messages.json"

    def __init__(self):
        """
        Set up this object to either do push notifications via Pushover,
        or SMS via Twilio,
        whichever is specified in the constants
        """
        self.log(f"Messaging Agent is initializing")
        self.pushover_user = os.getenv('PUSHOVER_USER', 'your-pushover-user-if-not-using-env')
        self.pushover_token = os.getenv('PUSHOVER_TOKEN', 'your-pushover-user-if-not-using-env')
        self.claude = Anthropic()
        self.log("Messaging Agent has initialized Pushover and Claude")

    def push(self, text):
        """
        Send a Push Notification using the Pushover API
        """
        self.log("Messaging Agent is sending a push notification")
        payload = {"user": self.pushover_user, "token": self.pushover_token, "message": text, "sound": "cashregister"}
        requests.post(self.pushover_url, data=payload)

    def alert(self, opportunity: Opportunity):
        """
        Make an alert about the specified Opportunity
        """
        text = f"Deal Alert! Price=${opportunity.deal.price:.2f}, "
        text += f"Estimate=${opportunity.estimate:.2f}, "
        text += f"Discount=${opportunity.discount:.2f} :"
        text += opportunity.deal.product_description[:10]+'... '
        text += opportunity.deal.url
        self.push(text)
        self.log("Messaging Agent has completed")

    def craft_message(self, description: str, deal_price: float, estimated_true_value: float) -> str:
        system_prompt = "You are given details of a great deal on special offer, "
        system_prompt += "and you summarise it in a short message of 2-3 sentences"
        user_prompt = "Please summarize this great deal in 2-3 sentences.\n"
        user_prompt += f"Item Description: {description}\nOffered Price: {deal_price}\nEstimated true value: {estimated_true_value}"
        user_prompt += "\n\nRespond only with the 2-3 sentence message which will be used to alert the user about this deal"
        message = self.claude.messages.create(
            model=self.MODEL,
            max_tokens=200,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ])
        return message.content[0].text

    def notify(self, description: str, deal_price: float, estimated_true_value: float, url: str):
        """
        Make an alert about the specified details
        """
        self.log("Messaging Agent is using Claude to craft the message")
        text = self.craft_message(description, deal_price, estimated_true_value)
        self.push(text[:200]+"... "+url)
        self.log("Messaging Agent has completed")
        
    
        