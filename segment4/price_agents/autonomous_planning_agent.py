from typing import Optional, List, Dict
from price_agents.agent import Agent as BaseAgent
from price_agents.deals import ScrapedDeal, DealSelection, Deal, Opportunity
from price_agents.scanner_agent import ScannerAgent
from price_agents.frontier_agent import FrontierAgent
from price_agents.specialist_agent import SpecialistAgent
from price_agents.messaging_agent import MessagingAgent
from agents import Agent, Runner, function_tool
import json
import asyncio
import os
from agents.mcp import MCPServerStdio

sandbox_path = os.path.abspath(os.path.join(os.getcwd(), "sandbox"))
files_params = {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path]}

planner = None

@function_tool
def scan_the_internet_for_bargains() -> str:
    """
    This tool scans the internet for bargains and returns a curated list of top deals
    """
    planner.log("Autonomous Planning agent is calling scanner")
    results = planner.scanner.scan(memory=planner.memory)
    return results.model_dump_json() if results else ""

@function_tool
def estimate_true_value(description: str) -> str:
    """
    This tool estimates the true value of a product based on a text description of it

    Args:
        description: a description of the product to be estimated
    """
    planner.log(f"Autonomous Planning agent is estimating value")
    estimate1 = planner.frontier.price(description)
    estimate2 = planner.specialist.price(description)
    estimate = (estimate1 + estimate2) / 2.0
    result = {"description": description, "estimated_true_value": estimate}
    return json.dumps(result)

@function_tool
def notify_user_of_deal(description: str, deal_price: float, estimated_true_value: float, url: str) -> str:
    """
    This tool notifies the user of a great deal, given a description of it, the price of the deal, and the estimated true value

    Args:
        description: a description of the product with the deal
        deal_price: how much the product is being offered for
        estimated_true_value: an estimate of how much this product is actually worth
        url: the web address of the product
    """
    if planner.opportunity:
        planner.log("Autonomous Planning agent is trying to notify the user a 2nd time; ignoring")
    else:
        planner.log("Autonomous Planning agent is notifying user")
        planner.messenger.notify(description, deal_price, estimated_true_value, url)
        deal = Deal(product_description=description, price=deal_price, url=url)
        discount = estimated_true_value - deal_price
        planner.opportunity = Opportunity(deal=deal, estimate=estimated_true_value, discount=discount)
    result = "notification sent"


class AutonomousPlanningAgent(BaseAgent):

    name = "Autonomous Planning Agent"
    color = BaseAgent.GREEN
    MODEL = "gpt-5"

    def __init__(self, collection):
        """
        Create instances of the 3 Agents that this planner coordinates across
        """
        self.log("Autonomous Planning Agent is initializing")
        self.scanner = ScannerAgent()
        self.frontier = FrontierAgent(collection)
        self.specialist = SpecialistAgent()
        self.messenger = MessagingAgent()
        self.memory = None
        self.opportunity = None
        self.log("Autonomous Planning Agent is ready")

    def get_tools(self):
        """
        Return the json for the tools to be used
        """
        return [scan_the_internet_for_bargains, estimate_true_value, notify_user_of_deal]

    system_message = """
Your mission is to find great deals on bargain products using your tools, and notify the user when you find them
by sending a push notification and by writing a file in markdown with a summary.
"""
    user_message = """
Your mission is to discover great deals on products. First you should use your tool to scan the internet for bargain deals.
Then for each deal, you should use your tool to estimate its true value - how much it's actually worth.
Finally, you should pick the single most compelling deal where the deal price is much lower than the estimated true value, 
and use your tool to send the user a push notification about that deal, and also use your tool to write this to the file sandbox/deals.md with a summary in markdown,
adding to the end of the file if it already exists.

You must only notify the user about one deal, and be sure to pick the most compelling deal, where the deal price is much lower than the estimated true value.
Only notify the user for the one best deal. Then just respond OK to indicate success."""
    
    messages = [{"role": "system", "content": system_message},{"role": "user", "content": user_message}]

    def run_async_task(self, coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        else:
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)

    async def go(self):
        async with MCPServerStdio(params=files_params, client_session_timeout_seconds=30) as server:
            agent = Agent(name="Planner", instructions=self.system_message, model=self.MODEL, tools=self.get_tools(), mcp_servers=[server])
            reply = await Runner.run(agent, self.user_message)
        return reply.final_output
        

    def plan(self, memory: List[str] = []) -> Optional[Opportunity]:
        """
        Run the full workflow, providing the LLM with tools to surface scraped deals to the user
        :param memory: a list of URLs that have been surfaced in the past
        :return: an Opportunity if one was surfaced, otherwise None
        """
        self.log("Autonomous Planning Agent is kicking off a run")
        self.memory = memory
        self.opportunity = None
        global planner # TODO find a better way to do this without globals!!
        planner = self
        reply = self.run_async_task(self.go())
        self.log(f"Autonomous Planning Agent completed with: {reply}")
        return self.opportunity