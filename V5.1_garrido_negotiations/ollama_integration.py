#!/usr/bin/env python3
"""
Ollama integration for V5_garrido_negotiations.

This script demonstrates how to integrate the three LLMs from Ollama_LLMs.
"""

import asyncio
import logging
import os
import sys
import subprocess
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ollama_integration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def create_ollama_models():
    """Create the Ollama models from the Modelfiles."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths to Modelfiles
    reader_of_offers_path = os.path.join(script_dir, 'Ollama_LLMs', 'Modelfile_reader_of_offers')
    reader_of_constrains_path = os.path.join(script_dir, 'Ollama_LLMs', 'Modelfile_reader_of_constrains')
    
    # Create the models
    try:
        logger.info("Creating reader_of_offers model...")
        subprocess.run(['ollama', 'create', 'reader_of_offers', '-f', reader_of_offers_path], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      text=True, 
                      check=True)
        
        logger.info("Creating reader_of_constrains model...")
        subprocess.run(['ollama', 'create', 'reader_of_constrains', '-f', reader_of_constrains_path], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      text=True, 
                      check=True)
        
        logger.info("Ollama models created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating Ollama models: {e}")
        return False

def list_ollama_models():
    """List available Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True, 
                               check=True)
        logger.info(f"Available Ollama models:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing Ollama models: {e}")
        return None

async def main():
    """Main function to demonstrate Ollama LLM integration."""
    print("Integrating Ollama LLMs for V5_garrido_negotiations...")
    
    # Check if Ollama is installed
    if not check_ollama_installed():
        print("Ollama is not installed. Please install Ollama from https://ollama.com")
        return
    
    print("Ollama is installed.")
    
    # List available models before creation
    print("\nAvailable models before creation:")
    list_ollama_models()
    
    # Create the models
    if create_ollama_models():
        print("\nOllama models created successfully!")
    else:
        print("\nFailed to create Ollama models. Please check the logs.")
        return
    
    # List available models after creation
    print("\nAvailable models after creation:")
    list_ollama_models()
    
    print("\nOllama LLM integration completed successfully!")
    print("\nYou can now use the following models in your hybrid negotiation system:")
    print("- reader_of_offers: For interpreting offers in negotiations")
    print("- reader_of_constrains: For understanding constraints in negotiations")
    print("- llama3: For generating responses in negotiations")

if __name__ == "__main__":
    asyncio.run(main())
