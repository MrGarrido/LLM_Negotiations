#!/usr/bin/env python3
"""
Main script for V5_garrido_negotiations.

This script implements the hybrid negotiation system that checks LLM outputs against
Pareto efficient allocations of price and quality.
"""

import asyncio
import argparse
import logging
import os
import sys
from typing import Dict, Any, List, Optional

from constants import C
from offer import Offer, OfferList
from pareto import pareto_efficient_string, pareto_efficient_offer, get_efficient_offers, pareto_efficient
from prompts import system_final_prompt, empty_offer_prompt,offer_without_quality_prompt,offer_without_price_prompt,not_profitable_prompt,offer_invalid, role_prompts, PROMPTS
from llm_client import LLMClient
from live_bargaining_system import LiveBargainingSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("hybrid_negotiation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HybridNegotiationSystem:
    """
    Hybrid negotiation system that checks LLM outputs against Pareto efficient allocations.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the hybrid negotiation system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.bot_role = config.get('bot_role', C.ROLE_SUPPLIER)
        self.constraint_bot = config.get('constraint_bot', 1)
        self.constraint_user = config.get('constraint_user', 10)
        self.max_greedy = config.get('max_greedy', False)
        
        # Initialize components
        self.llm_client = LLMClient(config)
        self.live_bargaining = LiveBargainingSystem(config)
        
        # Calculate Pareto efficient offers
        self.efficient_offers = get_efficient_offers(
            self.constraint_user, 
            self.constraint_bot, 
            self.bot_role
        )
        
        # Calculate profit threshold
        self.profit_threshold = pareto_efficient_offer(
            self.constraint_user,
            self.constraint_bot,
            self.bot_role,
            self.max_greedy
        )
        
        
        logger.info(f"Initialized hybrid negotiation system with bot role: {self.bot_role}")
        logger.info(f"Constraint user: {self.constraint_user}, Constraint bot: {self.constraint_bot}")
        logger.info(f"Profit threshold: {self.profit_threshold}, Max greedy: {self.max_greedy}")
        logger.info(f"Found {len(self.efficient_offers)} Pareto efficient offers")
    
    def is_profitable(self, offer: Offer) -> bool:
        """
        Check if an offer is profitable according to the profit threshold.
        
        Args:
            offer: Offer to check
            
        Returns:
            True if the offer is profitable, False otherwise
        """
        # Calculate profits if not already calculated
        if offer.profit_bot is None:
            offer.profits(self.bot_role, self.constraint_user, self.constraint_bot)
        
        return offer.profit_bot >= self.profit_threshold
    
    def is_pareto_efficient(self, offer: Offer) -> bool:
        """
        Check if an offer is Pareto efficient.
        
        Args:
            offer: Offer to check
            
        Returns:
            True if the offer is Pareto efficient, False otherwise
        """
        # Calculate profits if not already calculated
        if offer.profit_bot is None:
            offer.profits(self.bot_role, self.constraint_user, self.constraint_bot)
        
        return pareto_efficient(offer, self.efficient_offers)
    
    async def process_message(self, message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            message: User message
            
        Returns:
            Bot response
        """
        # Process the message using the live bargaining system
        response = await self.live_bargaining.process_message(message, self.llm_client)
        
        # Check if the last offer is Pareto efficient
        if self.live_bargaining.offer_list:
            last_offer = self.live_bargaining.offer_list[-1]
            if last_offer.is_valid:
                is_efficient = self.is_pareto_efficient(last_offer)
                is_profitable = self.is_profitable(last_offer)
                
                #logger.info(f"Last offer: Price={last_offer.price}, Quality={last_offer.quality}")
                #logger.info(f"Pareto efficient: {is_efficient}, Profitable: {is_profitable}")
                #logger.info(f"Bot profit: {last_offer.profit_bot}, User profit: {last_offer.profit_user}")
                
                # If the offer is not profitable, modify the response
                if not is_profitable:
                    logger.info("Offer is not profitable, modifying response")
                    
                    # Get Pareto efficient offers string
                    offers_pareto_efficient = pareto_efficient_string(
                        self.constraint_user, self.constraint_bot, self.bot_role
                    )
                    
                    # Format interactions for prompt
                    interactions_text = "\n".join(self.live_bargaining.interactions[-4:])
                    
                    # Format not profitable prompt
                    prompt = not_profitable_prompt(
                        self.config, message, offers_pareto_efficient, interactions_text
                    )
                    
                    # Generate new response
                    response = await self.llm_client.generate_response(prompt)
                    
                    # Update interactions
                    self.live_bargaining.interactions[-1] = f"Bot: {response}"
        
        return response
    
    async def run(self):
        """Run the hybrid negotiation system."""
        print("\n===== V5 Garrido Negotiations Hybrid System =====")
        print(f"Bot role: {self.bot_role}")
        print(f"Your role: {C.opposite(self.bot_role)}")
        print(f"Constraint User (Assigned): {self.constraint_user}")
        print("Type 'exit' to quit the negotiation.\n")
        
        # Initial message from bot
        response = await self.process_message("Start negotiation")
        print(f"\nBot: {response}")
        
        # Main negotiation loop
        while True:

            user_input = input("\nYou: ")
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nBot: Thank you for negotiating with me. Goodbye!")
                break

            # Process message
            response = await self.process_message(user_input)

            if "/conversation_ended" in response.strip():
                print(f"\nBot: {response}")
                print("\nBot: The conversation has ended. Hope you enjoyed the DEMO.")
                break
            else:
                print(f"\nBot: {response}")
            

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Hybrid negotiation system')
    
    parser.add_argument('--role', type=str, default='supplier',
                        choices=['buyer', 'supplier'],
                        help='Role of the bot (buyer or supplier)')
    
    parser.add_argument('--constraint-bot', type=int, default=1,
                        help='Constraint for the bot (production cost for supplier, market price for buyer)')
    
    parser.add_argument('--constraint-user', type=int, default=10,
                        help='Constraint for the user (market price for buyer, production cost for supplier)')
    
    parser.add_argument('--max-greedy', action='store_true',
                        help='Use maximum profit threshold instead of minimum')
    
    return parser.parse_args()


async def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Create configuration
    config = {
        'bot_role': args.role,
        'constraint_bot': args.constraint_bot,
        'constraint_user': args.constraint_user,
        'max_greedy': args.max_greedy,
        
        # LLM configuration
        'llm_host': os.environ.get('LLM_HOST', 'http://localhost:11434'),
        'llm_model': os.environ.get('LLM_MODEL', 'llama3'),
        'llm_reader': os.environ.get('LLM_READER', 'reader_of_offers'),
        'llm_constraint': os.environ.get('LLM_CONSTRAINT', 'reader_of_constrains'),
        'llm_temp': 0.2,
    }
    
    # Create and run the hybrid negotiation system
    system = HybridNegotiationSystem(config)
    await system.run()

if __name__ == "__main__":
    asyncio.run(main())
