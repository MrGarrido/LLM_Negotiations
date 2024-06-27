# LLM_Negotiations

This repository leverages Ollama.

1st install Ollama through https://ollama.com

2nd Run ollama in your terminal trough  
2nd Run the version of the you Pyhton script prefer (Negotiaton_LLM_VX.py)

## Arquitecture Iterations
**V0**:
  - **System** Prompt: Negotiation Context and Principles
  - **Introduction** Prompt: Max length, Be Proactive
  - **Follow up** Prompt: Conversation History, Attention to last Message
**V1**:_ (Changes)_
  - **System** Prompt: Rules, Combined Payoff (Price & Quality)
  - **Follow-up** User Prompt: Instruction based (1st 2nd and 3rd)
**V1.5**:
- **System** Prompt: Separate Payoffs one for Price and one for Quality
**V1.5.1**:
- **System** Prompt: Is loaded by using Modelfile principles with temperature of 0.2
  - https://github.com/ollama/ollama/blob/main/docs/modelfile.md   

