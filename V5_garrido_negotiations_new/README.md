#!/usr/bin/env python3
"""
README for V5_garrido_negotiations.

This file provides an overview of the V5_garrido_negotiations system.
"""

# V5_garrido_negotiations

A hybrid negotiation system that leverages LLMs to conduct negotiations while ensuring Pareto efficiency.

## Overview

V5_garrido_negotiations is a terminal-based negotiation system that uses Large Language Models (LLMs) to conduct negotiations. The system implements a hybrid approach that checks LLM outputs against Pareto efficient allocations of price and quality to ensure a minimum profit threshold.

The key flaw of this hybrid system is that it only enters this LLM output check if the user has provided a tangible offer. (Leading to an explotation prossibility)

## Features

- Terminal-based interface for easy interaction
- Integration with Ollama for local LLM inference
- Pareto efficiency check for all offers
- Support for both buyer and supplier roles
- Fixed response mode for testing and demonstration

## Installation

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

## System Architecture

The system consists of the following components:

1. **Constants**: Defines constants used throughout the system
2. **Offer**: Represents an offer in the negotiation system
3. **Pareto Efficiency**: Implements Pareto efficiency checks
4. **LLM Client**: Handles communication with the LLMs
5. **Prompt Manager**: Manages prompts for the LLMs
6. **Live Bargaining System**: Manages the negotiation process
7. **Hybrid Negotiation System**: Integrates all components and checks LLM outputs against Pareto efficient allocations

## License

MIT License
