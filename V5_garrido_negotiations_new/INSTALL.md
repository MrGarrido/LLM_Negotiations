#!/usr/bin/env python3
"""
Installation guide for V5_garrido_negotiations.

This file provides installation instructions for the V5_garrido_negotiations system.
"""

# Installation Guide for V5_garrido_negotiations

This guide will help you install and set up the V5_garrido_negotiations hybrid negotiation system.

## Prerequisites

- Python 3.8 or higher
- Ollama (for LLM integration)

## Installation Steps

### 1. Install Ollama

First, install Ollama by following the instructions at [https://ollama.com](https://ollama.com).

### 2. Clone the Repository

```bash
git clone https://github.com/MrGarrido/LLM_Negotiations.git
cd V5_garrido_negotiations
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create Ollama Models

Run the Ollama integration script to create the required models:

```bash
python ollama_integration.py
```

This will create the following models:
- `reader_of_offers`: For interpreting offers in negotiations
- `reader_of_constrains`: For understanding constraints in negotiations

Make sure you also have `llama3` available in your Ollama installation.

## Running the System

### Basic Usage

Run the hybrid negotiation system:

```bash
python3 hybrid_negotiation.py --role supplier --constraint-bot 1 --constraint-user 10
```
"or python3 hybrid_negotiation.py --role buyer --constraint-bot 9 --constraint-user 2"

Available options:
- `--role`: Role of the bot (buyer or supplier), default is supplier
- `--constraint-bot`: Constraint for the bot (production cost for supplier, market price for buyer), default is 1
- `--constraint-user`: Constraint for the user (market price for buyer, production cost for supplier), default is 10
- `--max-greedy`: Use maximum profit threshold instead of minimum
- `--fixed-responses`: Fixed responses for testing

## Troubleshooting

If you encounter any issues:

1. Make sure Ollama is running
2. Verify that the required models are created
3. Check the log files for error messages
4. Make sure all dependencies are installed correctly

For more information, please refer to the README.md file.
