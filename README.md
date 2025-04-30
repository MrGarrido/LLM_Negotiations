# LLM_Negotiations

This repository shows the initial steps in the development of the NegoBot leveraged in my first PhD experiment it leverages Ollama.

**V5.1** is the most recent release and has a dedicated README with instructions on how to use it.
 
## The following steps are tailored to V0 to V4 (Rudimentary)

1st install Ollama through https://ollama.com

2nd Check if ollama is active in your terminal through

ollama run llama3
you can enter /bye and proceed...

3rd Paste this line of code in yout terminal to create a tailored LLM named "reader"

ollama create reader -f ./V2_Reviewing_potential_offers/Modelfile 

Finally, Run the version of the you Pyhton script prefer (Negotiaton_LLM_VX.py)

V4 also requires the input: ollama create constrain_reader -f./V4_Understanding_Constrain/Modelfile_reader_of_constrains

## The actual system used in this experiment can be tested in V5_garrido_negotiations_new

To try it out in your terminal follow the steps in V5_garrido_negotiations_new/README.md


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
    - Regular: Bot will only accept offers that yield a profit **higher or equal** to the **minimum** profit in the pareto efficient frontier. 
- This version requires the ollama Models constrain_reader and reader, check OllamaCode.txt to install them. 

### **V5**:
The system implements a hybrid approach that checks LLM outputs against Pareto efficient allocations of price and quality to ensure a minimum profit threshold.
- Note that this system only enters this check if the user has provided a tangible offer.
    - Flaw: This flaw is corrected in the next version. However, the first experiment used this version. 

### **V5.1**:
The key improvement to the hybrid system resides in its ability to **always** check if the LLM output contains a reference to both negotiation terms (price and quality) and whether these terms are profitable enough at the greed level determined by the Pareto efficient function.

The fallback mechanism first attempts to generate a message to the counterpart using a prompt based on the counterpart reply (up to two times), re-generating it whenever an bad offer is detected. After 2 attempts it will try a third time with a different basic prompt (in case the counterpart's reply was corrupt). Finally, if all 3 attempts fail to produce an acceptable offer, it selects the offer with the highest profit from all previous generations.

### Dynamic Prompting:
![Prompting_strategy](https://github.com/user-attachments/assets/4287653f-bc49-46ec-b6f1-11643bbc5f8b)
System prompt has three components:
- Describes agent role (buyer/supplier).
- Set of negotiation issues (Price & Quality) and their respective payoffs.
- Negotiation protocol rules.

#### Why do we need a dynamic prompt?
- Every negotiation round has a random constraint (i.e., Procution Cost {1,2,3}) which determines the cost structure, thus, the payoffs described in the **system prompt** need to be calculated for the random constraint. 
- The user prompt is adapted based on the counterpart message. Sometimes the system should counter-offer, or accept the offer, or remind the user of the use of the interface.
  - How? We systematically combine the output from two LLMs prompted as Offer Reader and Constraint Reader to assess the required chatbot response (i.e., offer acceptance, counteroffer).
- During the negotiation conversation the dialogue is fed via user prompts with instructions to remember the negotiation rules, payoffs, and conversation history. Additionally, we leveraged in-context learning with few-shot examples of desired replies to user messages.

### Hybrid (Rule-Base + LLM):
![Hybrid](https://github.com/user-attachments/assets/6cb3a64d-95fa-4968-9bfd-5df1f2736d3b)
#### Offer Acceptance
The offer acceptance mechanism does not leverage generative AI, is purely rule-based.
- If the offer from the counterpart yields an acceptable profit, then the chatbot thanks the counterpart and the negotiation automatically ends with an agreement.
- What makes an offer acceptable? It must yield a pareto efficient profit or higher. Note that for an offer to be pareto efficient, the combination of price and quality has to maximize common profit while minimizing individual profit differences.

#### Offer Making
Applies a rule-based check on the profitability of the LLM generated message before sending it to the counterpart. 

1. LLM generates a **tentative** response message with a tangible offer (Needs to quote: Price & Quality). 
2. If the profit extracted from the **tentative** counteroffer message is not pareto efficient, then there is a loop that forces the chatbot to **generate another tentative** message. 
3. The 2nd step is repeated up to three times, if no offer yields a pareto efficient profit or higher, then chatbot replies with a message with the best offer among the worst.




