A hybrid negotiation system that leverages LLMs to conduct negotiations while ensuring Pareto efficiency.

## Overview

V5.1_garrido_negotiations is a terminal-based negotiation system that uses Large Language Models (LLMs) to conduct negotiations. The system implements a hybrid approach that checks LLM outputs against Pareto efficient allocations of price and quality to ensure a minimum profit threshold.

The key improvement to the hybrid system resides in its ability to **always** check if the LLM output contains a reference to both negotiation terms (price and quality) and whether these terms are profitable enough at the greed level determined by the Pareto efficient function.

The fallback mechanism first attempts to generate a message to the counterpart using a prompt based on the counterpart reply (up to two times), re-generating it whenever an bad offer is detected. After 2 attempts it will try a third time with a different basic prompt (in case the counterpart's reply was corrupt). Finally, if all 3 attempts fail to produce an acceptable offer, it selects the offer with the highest profit from all previous generations.

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
cd V5.1_garrido_negotiations
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

## Dynamic Prompting:
![Prompting_strategy](https://github.com/user-attachments/assets/4287653f-bc49-46ec-b6f1-11643bbc5f8b)
System prompt has three components:
- Describes agent role (buyer/supplier).
- Set of negotiation issues (Price & Quality) and their respective payoffs.
- Negotiation protocol rules.

### Why do we need a dynamic prompt?
- Every negotiation round has a random constraint (i.e., Procution Cost {1,2,3}) which determines the cost structure, thus, the payoffs described in the **system prompt** need to be calculated for the random constraint. 
- The user prompt is adapted based on the counterpart message. Sometimes the system should counter-offer, or accept the offer, or remind the user of the use of the interface.
  - How? We systematically combine the output from two LLMs prompted as Offer Reader and Constraint Reader to assess the required chatbot response (i.e., offer acceptance, counteroffer).
- During the negotiation conversation the dialogue is fed via user prompts with instructions to remember the negotiation rules, payoffs, and conversation history. Additionally, we leveraged in-context learning with few-shot examples of desired replies to user messages.

## Hybrid (Rule-Base + LLM):
![Hybrid](https://github.com/user-attachments/assets/6cb3a64d-95fa-4968-9bfd-5df1f2736d3b)
#### Offer Acceptance
The offer acceptance mechanism does not leverage generative AI, is purely rule-based.
- If the offer from the counterpart yields an acceptable profit, then the chatbot thanks the counterpart and the negotiation automatically ends with an agreement.
- What makes an offer acceptable? It must yield a pareto efficient profit or higher. Note that for an offer to be pareto efficient, the combination of price and quality has to maximize common profit while minimizing individual profit differences.

### Offer Making
Applies a rule-based check on the profitability of the LLM generated message before sending it to the counterpart. 

1. LLM generates a **tentative** response message with a tangible offer (Needs to quote: Price & Quality). 
2. If the profit extracted from the **tentative** counteroffer message is not pareto efficient, then there is a loop that forces the chatbot to **generate another tentative** message. 
3. The 2nd step is repeated up to three times, if no offer yields a pareto efficient profit or higher, then chatbot replies with a message with the best offer among the worst.

## License
MIT License



