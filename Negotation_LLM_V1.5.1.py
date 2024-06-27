import ollama

system_prompt = open('/Users/klausgarridotenorio/Desktop/Llama3/V1.5_Prompts/system_prompt_with_payoffs_and_rules.txt', 'r').read()
initial_prompt = open('/Users/klausgarridotenorio/Desktop/Llama3/V1.5_Prompts/intro_user_prompt.txt', 'r').read()
follow_up_prompt_1st = open('/Users/klausgarridotenorio/Desktop/Llama3/V1.5_Prompts/follow_up_user_prompt_first_part.txt', 'r').read()
follow_up_prompt_2nd = open('/Users/klausgarridotenorio/Desktop/Llama3/V1.5_Prompts/follow_up_user_prompt_intermediate.txt', 'r').read()

def extract_content(response):
    # This function extracts the message between quotation marks
    if 'message' in response and 'content' in response['message']:
        content = response['message']['content']
        # Find the position of the first and last quote
        start = content.find('"') + 1
        end = content.rfind('"')
        if start > 0 and end > start:
            return content[start:end]
        else:
            return content  # Return the whole content if no quotes are found
    return "Unexpected response format:" + response['message']['content']

def main():
    # First bot-initiated message
    init_message = {"role": "user","content": initial_prompt}
    
    # Send the initial message to ollama
    response = ollama.chat(
        model='negotiator', 
        messages=[
				{"role": "user","content": initial_prompt}
			,]
    )

    # Print the bot's response
    print(response['message']['content'])
    
    # Store conversation history
    interactions = [{"role": "system", "content": response['message']['content']}]
    
    # Allow user to continue the conversation
    while True:
        user_message = input("Your response (type 'exit' to end): ")
        if user_message.lower() == 'exit':
            print("Negotiation ended.")
            break
        interactions.append({"role": "user", "content": user_message})
        
        # Prepare and send follow-up message
        follow_up_content = follow_up_prompt_1st + user_message + follow_up_prompt_2nd + str(interactions)
        follow_up_content = follow_up_prompt_1st + user_message + follow_up_prompt_2nd + str(interactions)
        follow_up_response = ollama.chat(
            model='llama3', 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": follow_up_content}
            ]
        )
        
        print(extract_content(follow_up_response))

        # Print the bot's follow-up response
        #print(response['message']['content'])

if __name__ == "__main__":
    main()
