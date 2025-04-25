"""
LLM client for the V5_garrido_negotiations system.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional

import httpx
from ollama import AsyncClient
from prompts import PROMPTS, system_final_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMClient:
    """
    Client for interacting with LLMs in the hybrid negotiation system.
    """
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LLM client.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.client = None
        
        # Set default configuration
        self.llm_host = self.config.get('llm_host', os.environ.get('LLM_HOST', 'http://localhost:11434'))
        self.llm_user = self.config.get('llm_user', os.environ.get('LLM_USER', ''))
        self.llm_pass = self.config.get('llm_pass', os.environ.get('LLM_PASS', ''))
        self.llm_model = self.config.get('llm_model', os.environ.get('LLM_MODEL', 'llama3'))
        self.llm_reader = self.config.get('llm_reader', os.environ.get('LLM_READER', 'reader_of_offers'))
        self.llm_constraint = self.config.get('llm_constraint', os.environ.get('LLM_CONSTRAINT', 'reader_of_constrains'))
        self.llm_temp = self.config.get('llm_temp', 0.2)
        
        logger.info(f"Initialized LLM client with host: {self.llm_host}")
        logger.info(f"Using models: {self.llm_model}, {self.llm_reader}, {self.llm_constraint}")
    
    def _ensure_client(self):
        """Ensure the client is initialized."""
        if self.client is None:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            auth = None
            if self.llm_user and self.llm_pass:
                auth = httpx.BasicAuth(username=self.llm_user, password=self.llm_pass)
            self.client = AsyncClient(host=self.llm_host, auth=auth)
    
    async def generate_response(self, content: str) -> str:
        """
        Generate a response using the main LLM.
        
        Args:
            content: Content to send to the LLM
            
        Returns:
            Generated response
        """
        # Ensure client is initialized
        self._ensure_client()
        
        # Prepare system prompt
        #system_prompt = self._get_system_prompt()

        system_prompt = system_final_prompt(self.config)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        try:
            # Call LLM
            response = await self.client.chat(
                model=self.llm_model,
                options={'temperature': self.llm_temp},
                messages=messages
            )
            
            # Extract content
            llm_output = self._extract_content(response)
            
            return llm_output
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error while generating a response."
    
    async def interpret_constraint(self, content: str) -> str:
        """
        Interpret a constraint using the constraint reader LLM.
        
        Args:
            content: Content to send to the LLM
            
        Returns:
            Interpreted constraint
        """
        # Ensure client is initialized
        self._ensure_client()
        
        # Prepare messages
        messages = [{'role': 'user', 'content': content}]
        
        try:
            # Call LLM
            response = await self.client.chat(
                model=self.llm_constraint,
                messages=messages
            )
            
            # Extract content
            llm_output = response['message']['content']
            
            return llm_output
        except Exception as e:
            logger.error(f"Error interpreting constraint: {e}")
            return ""
    
    async def interpret_offer(self, content: str) -> str:
        """
        Interpret an offer using the offer reader LLM.
        
        Args:
            content: Content to send to the LLM
            
        Returns:
            Interpreted offer
        """
        # Ensure client is initialized
        self._ensure_client()
        
        # Prepare messages
        messages = [{'role': 'user', 'content': PROMPTS['understanding_offer'] + content}]
        
        try:
            # Call LLM
            response = await self.client.chat(
                model=self.llm_reader,
                messages=messages
            )
            
            # Extract content
            llm_output = response['message']['content']
            
            return llm_output
        except Exception as e:
            logger.error(f"Error interpreting offer: {e}")
            return ""
        
    
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the main LLM.
        
        Returns:
            System prompt
        """
        # Load system prompt from file
        system_prompt_path = os.path.join(
            os.path.dirname(__file__), 
            'prompts', 
            'system_prompt_with_payoffs_and_rules.txt'
        )
        
        try:
            with open(system_prompt_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Error loading system prompt: {e}")
            return "You are a negotiation assistant. Help the user negotiate effectively."
    
    def _extract_content(self, response: Dict[str, Any]) -> str:
        """
        Extract content from LLM response.
        
        Args:
            response: LLM response
            
        Returns:
            Extracted content
        """
        def remove_inner(string: str, start_char: str, end_char: str):
            while start_char in string and end_char in string:
                start_pos = string.find(start_char)
                end_pos = string.find(end_char, start_pos) + 1
                if 0 <= start_pos < end_pos:
                    string = string[:start_pos] + string[end_pos:]
                else:
                    break
            return string
        
        try:
            content: str = response['message']['content'].strip()
        except KeyError:
            logger.error(f"Unexpected response format: {response}")
            return f"Unexpected response format: {response}"
        
        # Extract text within quotes if quotes are found
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
