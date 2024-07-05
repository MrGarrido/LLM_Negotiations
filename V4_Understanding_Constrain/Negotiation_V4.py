import ollama
import re

system_prompt = open('./V4_Understanding_Constrain/Prompts/system_prompt_V4.txt', 'r').read()
initial_prompt = open('./V4_Understanding_Constrain/Prompts/intro_user_prompt.txt', 'r').read()

def extract_content(response):
    # This function extracts the message between quotation marks
    if 'message' in response and 'content' in response['message']:
        content = response['message']['content']

        # Remove text before the first colon
        if ':' in content:
            content = content.split(':', 1)[1].strip()
        
        # Find the position of the first and last quote
        start = content.find('"') + 1
        end = content.rfind('"')
        
        # Remove text within parentheses if no quotes are found
        while '(' in content and ')' in content:
            start = content.find('(')
            end = content.find(')', start) + 1
            if start >= 0 and end > start:
                content = content[:start] + content[end:]
        return content.strip()  # Return the cleaned content
    return response['message']['content']

def reader_of_constrains(message):

    understandign_offer = ollama.chat(
        model='constrain_reader', 
        messages=[{"role": "user","content": "Here is the negotatior message you need to read: " + message}]
    )

    # Regular expression to find the pattern [Price, Quality]
    pattern = r'\[.*?\]'

    # Search for the pattern in the message
    match_constrain = re.search(pattern, understandign_offer['message']['content'])

    return(match_constrain.group(0))

def double_check_of_constrain(constrain, loops):

    if loops<1:
        if not constrain:  # Check if constrain is an empty list
            loops=+1
            return "I did not quite understand the constrain. Please clarify your profit constrain."
            
        if isinstance(constrain, (int, float)):  # Check if constrain is an integer or float
            loops=+1
            return f"Confirming: Is {constrain} the correct constrain?"
        loops=+1
        return "I did not quite understand the constrain. Please clarify your profit constrain."
    else:
        
        if isinstance(constrain, (int, float)):  # Check if constrain is an integer or float
            return ("LLM ASKS FOR PRICE AND QUALITY IDEAL SCENARIO",constrain)
        else:
            #RANDOMLY DRAWN CONSTRAIN FROM UNIFORM DISTRIBUTION
            return ("LLM ASKS FOR PRICE AND QUALITY IDEAL SCENARIO",8)

loops=0
def main():
    
    # Send the initial message to ollama
    response = ollama.chat(
        model='llama3', 
        messages=[
				{"role": "system", "content": system_prompt},
				{"role": "user","content": initial_prompt}
			,]
    )


    # Print the bot's response
    print(extract_content(response))
    
    # Store conversation history
    interactions = [{"role": "system", "content": response['message']['content']}]

    offers={}
    constrain_of_counterpart = []
    loops=0
    # Allow user to continue the conversation
    while True:
        user_message = input("Your response (type 'exit' to end): ")
        if user_message.lower() == 'exit':
            print("Negotiation ended.")
            break
        interactions.append({"role": "user", "content": user_message})
        print(interactions)
        #Last message sent my user
        last_item_content = interactions[-1]['content']
        #Constrain share by the user
        constrain_user= reader_of_constrains(last_item_content)
        print(constrain_user)
        if loops<1:
            if not constrain_user:  # Check if constrain is an empty list
                loops=+1
                print("I did not quite understand the constrain. Please clarify your profit constrain.")
                
            elif isinstance(constrain_user[0], (int, float)):  # Check if constrain is an integer or float
                loops=+1
                print(f"Confirming: Is {constrain_user[0]} the correct constrain?")
            else:
                loops=+1
                print("I did not quite understand the constrain. Please clarify your profit constrain.")
        else:
        
            if isinstance(constrain_user[0], (int, float)):  # Check if constrain is an integer or float
                print("LLM ASKS FOR PRICE AND QUALITY IDEAL SCENARIO",constrain_user[0])
            else:
                #RANDOMLY DRAWN CONSTRAIN FROM UNIFORM DISTRIBUTION
                print("LLM ASKS FOR PRICE AND QUALITY IDEAL SCENARIO",8)

if __name__ == "__main__":
    main()   