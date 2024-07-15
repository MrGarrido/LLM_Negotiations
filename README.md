# LLM_Negotiations

This repository leverages Ollama.

1st install Ollama through https://ollama.com

2nd Run ollama in your terminal through

ollama run llama3

3rd Paste this line of code in yout terminal to create a tailored LLM named "reader"

ollama create reader -f ./V2_Reviewing_potential_offers/Modelfile 

Finally, Run the version of the you Pyhton script prefer (Negotiaton_LLM_VX.py)

V4 also requires the input: ollama create constrain_reader -f./V4_Understanding_Constrain/Modelfile_reader_of_constrains




## Arquitecture Iterations

### **V0**:
  - **System** Prompt: Negotiation Context and Principles
  - **Introduction** Prompt: Max length, Be Proactive
  - **Follow up** Prompt: Conversation History, Attention to last Message
    
### **V1**:_ (Changes)_
  - **System** Prompt: Rules, Combined Payoff (Price & Quality)
  - **Follow-up** User Prompt: Instruction based (1st 2nd and 3rd)
    
### **V1.5**:
- **System** Prompt: Separate Payoffs one for Price and one for Quality
  
### **V1.5.1**:
- **System** Prompt: Is loaded by using Modelfile principles with temperature of 0.2
  - https://github.com/ollama/ollama/blob/main/docs/modelfile.md

### **V2**:
- **NEW AGENT**: Main task is understand the offer and output the Price and Quality
- **Rule-Based on User**: If-Else Statement evaluates the profitability and prepares tailored prompts
- **The V1.5 Agent**: Receives the (Human Designed) profit evaluation to reply to the counterpart accordingly.

### **V3**:
- **Rule-Based on both User and Bot**: If-Else Statement evaluates the profitability of the offer of the user and bot and prepares tailored prompts

### **V4**:
- **Totally NEW Bot Led**: Understand the constrain of the counterpart first
- **Actively ask for the user Ideal P & Q combination**: Improved check of best offer within the bot loop (now it contrasts against the best user offer)
- **Directly calculate the user profitability and own**: Stored in separate dictionaries (Next step is pareto efficient bidding strategy)

### **V4.5**:
- **Pareto Efficieng Bidding Strategy**: Leverage the profit function to send offers that are maximizing the bot profits while finding a common balanced ground. 
- **Bot Prompts Adapted to BOTH Roles**: Now the prompting is dynamic based on the bot role and their constrain value. 
- **Offers Acceptance Is Greedy or Regular**: 
    - Greedy: Bot will only accept offers that yield a profit **higher or equal** to the **maximum** profit in the pareto efficient frontier. 
    - Regualar: Bot will only accept offers that yield a profit **higher or equal** to the **minimum** profit in the pareto efficient frontier. 
- This version requires the ollama Models constrain_reader and reader, check OllamaCode.txt to install them. 
