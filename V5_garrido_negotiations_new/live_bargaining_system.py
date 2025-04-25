"""
Live bargaining system for the V5_garrido_negotiations system.
"""

import asyncio
import random

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from constants import C
from offer import Offer, OfferList, ACCEPT, NOT_PROFITABLE, OFFER_QUALITY, OFFER_PRICE, NOT_OFFER, INVALID_OFFER
from pareto import pareto_efficient_string, pareto_efficient_offer
from prompts import system_final_prompt, empty_offer_prompt,offer_without_quality_prompt,offer_without_price_prompt,not_profitable_prompt,offer_invalid, role_prompts, PROMPTS
from llm_client import LLMClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class LiveBargainingSystem:
    """
    System for managing live bargaining interactions in the hybrid negotiation system.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the live bargaining system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.bot_role = config.get('bot_role', C.ROLE_SUPPLIER)
        self.constraint_bot = config.get('constraint_bot', 1)
        self.constraint_user = config.get('constraint_user', 10)
        self.max_greedy = config.get('max_greedy', False)
        
        # Initialize state
        self.offer_list = OfferList()
        self.interactions = []
        self.constraint_set = False
        self.profit_threshold = None
        self.calculate_profit_threshold()
        
        logger.info(f"Initialized live bargaining system with bot role: {self.bot_role}")
        logger.info(f"Constraint user: {self.constraint_user}, Constraint bot: {self.constraint_bot}")
        logger.info(f"Profit threshold: {self.profit_threshold}, Max greedy: {self.max_greedy}")
    
    def calculate_profit_threshold(self):
        """Calculate the profit threshold for Pareto efficient offers."""
        self.profit_threshold = pareto_efficient_offer(
            self.constraint_user,
            self.constraint_bot,
            self.bot_role,
            self.max_greedy
        )
        logger.info(f"Calculated profit threshold: {self.profit_threshold}")

    def constraint_in_range(self, constraint_user: Optional[int]) -> bool:
            if constraint_user is None:
                return False

            user_role = C.opposite(self.bot_role)
            # User is Supplier, constrain to production cost
            if user_role == C.ROLE_SUPPLIER:
                return 1 <= constraint_user <= 3
            # User is Buyer, constrain to market price
            else:
                return 8 <= constraint_user <= 10
            
    def constant_draw_constraint(self) -> int:
        # Randomly draw constraint for the user
        user_role = C.opposite(self.bot_role)
        if user_role == C.ROLE_SUPPLIER:
            return 1 # Min constraint Production cost
        else:
            return 10 # Max constraint Selling Price
        
    def add_profits(self, offer: Offer):
        offer.profits(self.bot_role, self.constraint_user, self.constraint_bot)

    def get_greediness(self, constraint_user: int, constraint_bot: int) -> int:
        if constraint_user not in (0, None):
            return pareto_efficient_offer(constraint_user, constraint_bot,
                                          self.bot_role, self.max_greedy)
        else:
            return 3 # Default greedy value

    def extract_content(self, content) -> str:
        def remove_inner(string: str, start_char: str, end_char: str):
            while start_char in string and end_char in string:
                start_pos = string.find(start_char)
                end_pos = string.find(end_char, start_pos) + 1
                if 0 <= start_pos < end_pos:
                    string = string[:start_pos] + string[end_pos:]
                else:
                    break
            return string

        # Extract text within the quotes if quotes are found
        if content.count('"') > 1:
            start = content.find('"') + 1
            end = content.rfind('"')
            content = content[start:end]
        else:
            # Remove 'System" starts
            if content.lower().startswith("system:"):
                content = content[7:].strip()
            if content.lower().startswith("system,"):
                content = content[7:].strip()

        # Remove text within parentheses if no quotes are found
        content = remove_inner(content, '(', ')')
        # Remove content within square brackets
        content = remove_inner(content, '[', ']')

        # Remove text before "list_of_offers_to_choose_from"
        if 'list_of_offers_to_choose_from' in content:
            split_list = content.split('list_of_offers_to_choose_from:', 1)
            content = split_list[1].strip() if len(split_list) > 1 else content

        # Remove text before the first colon
        if ':' in content:
            split_list = content.split(':', 1)
            content = split_list[1].strip() if len(split_list) > 1 else content

        # Split the content at line breaks and take only the first part
        content = content.split('\n', 1)[0]

        return content.strip()

    def get_respond_prompt(self, evaluation: str, message:str) -> str:
        if evaluation == NOT_OFFER:
            return empty_offer_prompt(
                self.config, message,
                self.offers_pareto_efficient, str(self.interactions))
        elif evaluation == OFFER_QUALITY:
            return offer_without_price_prompt(
                self.config, message,
                self.offers_pareto_efficient, str(self.interactions))
        elif evaluation == OFFER_PRICE:
            return offer_without_quality_prompt(
                self.config, message,
                self.offers_pareto_efficient, str(self.interactions))
        elif evaluation == INVALID_OFFER:
            return offer_invalid(self.config, message)
        else:
            return not_profitable_prompt(
                self.config, message,
                self.offers_pareto_efficient, str(self.interactions))
    
    async def process_message(self, message: str, llm_client: LLMClient) -> str:
        #  print(len(self.interactions),self.interactions ) Debugging can be deleted
        """
        Process a user message and generate a response.
        
        Args:
            message: User message
            llm_client: LLM client
            
        Returns:
            Bot response
        """
        # Add message to interactions
        self.interactions.append(f"User: {message}")
        
        # Check if this is the first message
        if len(self.interactions) == 1:
            return await self.output_first_message()
        
        # Check if we need to set the constraint
        if len(self.interactions) == 2:
            return await self.handle_constraint_message(message, llm_client)
        
        # Check if we need to set the constraint
        if len(self.interactions) == 3:
            return await self.handle_constraint_message_double_check(message, llm_client)
        if len(self.interactions) > 3:
        # Process the message as a negotiation message
            return await self.handle_negotiation_message(message, llm_client)
    
    async def output_first_message(self) -> str:
        """
        Outputs first message from the user. Scripted)
            
        Returns:
            Bot response
        """
        # Get the initial prompt
        if self.bot_role == C.ROLE_BUYER:
            initial_prompt = PROMPTS['first_message_PC']
        else:
            initial_prompt = PROMPTS['first_message_MP']     
        return initial_prompt

    async def handle_constraint_message(self, message: str, llm_client: LLMClient) -> str:
        """
        Handle the first message from the user which should contain the user's constraint.
        
        Args:
            message: User message
            llm_client: LLM client
            
        Returns:
            Bot response
        """
        # Try to interpret the constraint
        constraint_text = await llm_client.interpret_constraint(message)
        
        # Extract constraint using regex
        constraint_match = C.PATTERN_CONSTRAINT.search(constraint_text)
        
        context_constraint = PROMPTS['context_constraint'][self.bot_role]   
            
        if constraint_match:
            # Set the constraint
            self.constraint_user = int(constraint_match.group(1))
            if self.constraint_in_range(self.constraint_user):
                params = (self.constraint_user, context_constraint) * 2
                message = PROMPTS['constraint_confirm'] % params
                return message
            else:
                message = PROMPTS['constraint_clarify'] % context_constraint
                return message
        else:
            message = PROMPTS['constraint_clarify'] % context_constraint
            return message
        
    async def handle_constraint_message_double_check(self, message: str, llm_client: LLMClient) -> str:
        """
        Handle the second message from the user which should contain the user's constraint.
        
        Args:
            message: User message
            llm_client: LLM client
            
        Returns:
            Bot response
        """
        # Try to interpret the constraint
        constraint_text = await llm_client.interpret_constraint(message)
        
        # Extract constraint using regex
        constraint_match = C.PATTERN_CONSTRAINT.search(constraint_text)
        
        context_constraint = PROMPTS['context_constraint'][self.bot_role]   
            
        if constraint_match:
            # Set the constraint
            self.constraint_user = int(constraint_match.group(1))
            if self.constraint_in_range(self.constraint_user):

                if self.bot_role == C.ROLE_BUYER:
                    message = PROMPTS['constraint_final_supplier']
                else:
                    message = PROMPTS['constraint_final_buyer']
                return message
            else:
                if self.bot_role == C.ROLE_BUYER:
                    message = PROMPTS['constraint_persist_final_supplier']
                else:
                    message = PROMPTS['constraint_persist_final_buyer']
                final_constraint = self.constant_draw_constraint() 
                self.constraint_user = final_constraint
                return message
        else:
            if self.bot_role == C.ROLE_BUYER:
                message = PROMPTS['constraint_persist_final_supplier']
            else:
                message = PROMPTS['constraint_persist_final_buyer']
            final_constraint = self.constant_draw_constraint()
            self.constraint_user = final_constraint
            return message

    async def accept_offer(self, message: str, llm_client: LLMClient) -> str:
            
        content = PROMPTS['accept_from_interface'] + message

        response = await llm_client.generate_response(content)
        
        return response    
    
    async def respond_to_non_offer(self, evaluation: str, message: str, llm_client: LLMClient) -> str:
        # Difference between Version 1.0 and 1.1 here we dont check the LLM output. but in 1.1 we allways check it.
        def get_offer_in_terms_of_price_quality(offer_text: str) -> Optional[Offer]:
            """
            Extract offer in terms of price and quality from the offer text.
            
            Args:
                offer_text: Offer text
                
            Returns:
                Offer object with price and quality
            """
            def get_int(p) -> Optional[int]:
                try:
                    return round(
                        float("".join(s for s in p if s.isdigit() or s == '-')))
                except ValueError:
                    pass
            # Regular expression to find the pattern [Price, Quality]
            price = quality = None
            match_list = list(C.PATTERN_OFFER.finditer(offer_text))
            for match in reversed(match_list):
                parts = [part.replace('<', '').replace('>', '').strip()
                        for part in match.group(1).split(',')]
                ints = [get_int(part.replace('€', '')) for part in parts]

                if len(ints) == 1:
                    price = quality = None
                elif len(ints) == 2:
                    price, quality = ints
                    break
                elif len(ints) == 3:
                    if ints[0] is not None and ints[2] is not None:
                        price, quality = ints[0], ints[2]
                        break
                    elif ints[1:] == [None, None] and ints[0] is not None:
                        price = ints[0]
                        quality = None
                        break
                    elif ints[:2] == [None, None] and ints[2] is not None:
                        quality = ints[2]
                        price = None
                        break
                    elif ints == [None, None, None]:
                        price = None
                        quality = None
                    else:
                        price = quality = None
                else:
                    price = quality = None
            return Offer(idx=self.bot_role, price=price, quality=quality)
        
        content = self.get_respond_prompt(evaluation, message)
        response = await llm_client.generate_response(content)
        llm_output = self.extract_content(response)
        last_offer = await llm_client.interpret_offer(llm_output)
        last_offer = get_offer_in_terms_of_price_quality(last_offer)
        
        if last_offer.is_valid:
            self.add_profits(last_offer)
            self.offer_list.append(last_offer)
        if llm_output is not None:
            return llm_output
     
    async def respond_to_offer(self, evaluation: str, greedy: int, message: str, llm_client: LLMClient)-> str:

        def get_offer_in_terms_of_price_quality(offer_text: str) -> Optional[Offer]:
            """
            Extract offer in terms of price and quality from the offer text.
            
            Args:
                offer_text: Offer text
                
            Returns:
                Offer object with price and quality
            """
            def get_int(p) -> Optional[int]:
                try:
                    return round(
                        float("".join(s for s in p if s.isdigit() or s == '-')))
                except ValueError:
                    pass
            # Regular expression to find the pattern [Price, Quality]
            price = quality = None
            match_list = list(C.PATTERN_OFFER.finditer(offer_text))
            for match in reversed(match_list):
                parts = [part.replace('<', '').replace('>', '').strip()
                        for part in match.group(1).split(',')]
                ints = [get_int(part.replace('€', '')) for part in parts]

                if len(ints) == 1:
                    price = quality = None
                elif len(ints) == 2:
                    price, quality = ints
                    break
                elif len(ints) == 3:
                    if ints[0] is not None and ints[2] is not None:
                        price, quality = ints[0], ints[2]
                        break
                    elif ints[1:] == [None, None] and ints[0] is not None:
                        price = ints[0]
                        quality = None
                        break
                    elif ints[:2] == [None, None] and ints[2] is not None:
                        quality = ints[2]
                        price = None
                        break
                    elif ints == [None, None, None]:
                        price = None
                        quality = None
                    else:
                        price = quality = None
                else:
                    price = quality = None
            return Offer(idx=self.bot_role, price=price, quality=quality)

        content1 = self.get_respond_prompt(evaluation, message)
        content2 = self.get_respond_prompt("From_0", message)

        llm_offers = []
        last_offer = llm_output = None
        while len(llm_offers) < 3 and evaluation != ACCEPT:
            response = await llm_client.generate_response(content1)
            llm_output = self.extract_content(response)
            last_offer = await llm_client.interpret_offer(llm_output)
            last_offer = get_offer_in_terms_of_price_quality(last_offer)
            if not last_offer or not last_offer.is_complete:
                response = await llm_client.generate_response(content2)
                llm_output = self.extract_content(response)
                last_offer = await llm_client.interpret_offer(llm_output)
                last_offer = get_offer_in_terms_of_price_quality(last_offer)

            if last_offer.is_complete:
                self.add_profits(last_offer)
            else:
                last_offer.profit_bot = last_offer.profit_user = 0
            llm_offers.append([last_offer.profit_bot, llm_output, last_offer])
            evaluation = last_offer.evaluate(greedy)

        if evaluation != ACCEPT:
            max_profit = max(llm_offer[0] for llm_offer in llm_offers)
            best_offer = random.choice([llm_offer for llm_offer in llm_offers
                                        if llm_offer[0] == max_profit])
            _, llm_output, last_offer = best_offer

        if last_offer is not None:
            self.offer_list.append(last_offer)
        if llm_output is not None:
            return llm_output
        
    

    async def handle_negotiation_message(self, message: str, llm_client: LLMClient) -> str:
        """
        Handle a negotiation message from the user.
        
        Args:
            message: User message
            llm_client: LLM client
            
        Returns:
            Bot response
        """
        # Try to interpret the offer
        #constraint_text = await llm_client.interpret_constraint(message)
        offer_text = await llm_client.interpret_offer(message)

        def get_offer_in_terms_of_price_quality(offer_text: str) -> Optional[Offer]:
            """
            Extract offer in terms of price and quality from the offer text.
            
            Args:
                offer_text: Offer text
                
            Returns:
                Offer object with price and quality
            """
            def get_int(p) -> Optional[int]:
                try:
                    return round(
                        float("".join(s for s in p if s.isdigit() or s == '-')))
                except ValueError:
                    pass
            # Regular expression to find the pattern [Price, Quality]
            price = quality = None
            match_list = list(C.PATTERN_OFFER.finditer(offer_text))
            for match in reversed(match_list):
                parts = [part.replace('<', '').replace('>', '').strip()
                        for part in match.group(1).split(',')]
                ints = [get_int(part.replace('€', '')) for part in parts]

                if len(ints) == 1:
                    price = quality = None
                elif len(ints) == 2:
                    price, quality = ints
                    break
                elif len(ints) == 3:
                    if ints[0] is not None and ints[2] is not None:
                        price, quality = ints[0], ints[2]
                        break
                    elif ints[1:] == [None, None] and ints[0] is not None:
                        price = ints[0]
                        quality = None
                        break
                    elif ints[:2] == [None, None] and ints[2] is not None:
                        quality = ints[2]
                        price = None
                        break
                    elif ints == [None, None, None]:
                        price = None
                        quality = None
                    else:
                        price = quality = None
                else:
                    price = quality = None
            return Offer(idx=C.opposite(self.bot_role), price=price, quality=quality)

        #Extratct offer using regex
        last_offer= get_offer_in_terms_of_price_quality(offer_text)

        # Check if the offer is valid
        if last_offer.is_complete:
                # Add profits to the offer
                self.add_profits(last_offer)       
        else:
            last_offer.profit_bot = last_offer.profit_user = 0
        # Calculate the greediness
        greedy = self.get_greediness(self.constraint_user, self.constraint_bot)
       # print(f"Greediness: {greedy}")

        self.offers_pareto_efficient = pareto_efficient_string(
                self.constraint_user, self.constraint_bot, self.bot_role)
        #print(f"Pareto efficient offers: {self.offers_pareto_efficient}")
        # Evaluate the profitability of user offer and respond
        evaluation = last_offer.evaluate(greedy)
        #print("evaluation",evaluation)

        if evaluation == ACCEPT:
            return f"{await self.accept_offer(message, llm_client)} /conversation_ended"
        elif evaluation in (NOT_PROFITABLE, OFFER_PRICE, OFFER_QUALITY):
            return await self.respond_to_offer(evaluation, greedy,message, llm_client)
        elif evaluation in (INVALID_OFFER, NOT_OFFER):
            return await self.respond_to_non_offer(evaluation,message, llm_client)
        else:
            raise Exception

    