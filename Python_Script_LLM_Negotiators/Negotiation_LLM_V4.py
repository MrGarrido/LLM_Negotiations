import ollama
import re
import random

system_prompt = open('./V4_Understanding_Constrain/Prompts/system_prompt_V4.txt', 'r').read()
initial_prompt = open('./V4_Understanding_Constrain/Prompts/intro_user_prompt.txt', 'r').read()
non_profitable_offer = open('./V4_Understanding_Constrain/Prompts/non_profitable_increaseP_DecreaseQ.txt', 'r').read()
follow_up_prompt_2nd = open('./V4_Understanding_Constrain/Prompts/follow_up_user_prompt_intermediate.txt', 'r').read()

greedy=3
bot_role='supplier' # or 'buyer' 
if bot_role=='buyer':
    context_constrain='Production Cost (PC)'
    randomly_drawn=random.choice([1, 2, 3])
    bot_constrain=8
else:
    context_constrain= 'Selling Price to Consumer (SP)'
    randomly_drawn=random.choice([8, 9, 10])    
    bot_constrain=2


def extract_content(response):
    # This function extracts the message between quotation marks
    if 'message' in response and 'content' in response['message']:
        content = response['message']['content']

        # Remove text before the first colon
        if ':' in content:
            content = content.split(':', 1)[1].strip()
        
        # Split the content at line breaks and take only the first part NOT ACTIVE
        #content = content.split('\n', 1)[0]

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

def string_to_list(s): 
    # Remove the square brackets
    s = s.strip('[]')
    
    # Check if the resulting string is empty
    if not s:
        return ['']
    
    # Split the string by comma and convert each to an integer
    return [float(s)]

def reader_of_constrains(message):

    understandign_offer = ollama.chat(
        model='constrain_reader', 
        messages=[{"role": "user","content": "Here is the negotatior message you need to read: " + message}]
    )

    # Regular expression to find the pattern [Price, Quality]
    pattern = r'\[.*?\]'

    # Search for the pattern in the message
    match_constrain = re.search(pattern, understandign_offer['message']['content'])
    try:
        return (string_to_list(match_constrain.group(0)))
    except ValueError:
        return (match_constrain.group(0))

def reader_of_offers(message):

    understandign_offer = ollama.chat(
        model='reader', 
        messages=[{"role": "user","content": "Here is the negotatior message you need to read: " + message}]
    )

    # Regular expression to find the pattern [Price, Quality]
    pattern = r'\[([^\]]+)\]'

    # Search for the pattern in the message
    match = re.search(pattern, understandign_offer['message']['content'])

    try:
        match=match.group(1)
    except AttributeError:
        match = '[['', '']]'


    # Remove the brackets and split the string by comma
    elements = match.split(',')

    # Process each element to determine if it should be an integer or remain a string
    parsed_list = []
    for element in elements:
        if element.isdigit():
            parsed_list.append(int(element))  # Convert to integer if it's purely numeric
        else:
            parsed_list.append(element)      # Otherwise, keep as string
    
    quality = str(parsed_list[1]).strip()

    if quality != '':
        try: 
            quality= int(quality)
        except ValueError:
            quality = quality.replace('<', '').replace('>', '').strip()
            try:   
                quality = int(quality)
            except ValueError:
                if quality=='Quality':
                    quality=''
                else:
                    quality = quality  
    else:
        quality= quality

    price = str(parsed_list[0]).strip()
    if price != '':
        try:
            price = float(price.replace('€', '').strip()) 
        except ValueError:
            # Extract numeric value first, then handle '<' or '>'.
            price = price.replace('€', '').replace('<', '').replace('>', '').strip()
            try:   
                price = float(price)
            except ValueError:
                if price=='Price in Euros':
                    price=''
                else:
                    price = price  
    else:
        price= price
    
    clean_list= []
    clean_list.append([price,quality])

    return(clean_list)

def find_last_valid_quality(offers):
    # Iterate over the offers dictionary in reverse to find the last offer with a valid numerical quality
    for offer, profit in reversed(offers.items()):
        if offer[1] != '':
            return int(offer[1])  # Convert the quality to an integer and return it
    return 2  # Return 0 if no valid quality is found

def find_last_valid_price(offers):
    # Iterate over the offers dictionary in reverse to find the last offer with a valid numerical quality
    for offer, profit in reversed(offers.items()):
        if offer[0] != '':
            return float(offer[0])  # Convert the quality to an integer and return it
    return 5.5  # Return 0 if no valid quality is found

def move_key_to_end(offers, key):
    if key in offers:
        value = offers[key]
        del offers[key]  # Remove the key
        offers[key] = value  # Re-insert the key at the end

def profit_calculator(offer,offers,offers_profit_user,constrain_of_user):
    price= offer[0][0]
    quality=offer[0][1]
    constrain_user=constrain_of_user
    constrain_bot=bot_constrain

    if isinstance(price, str) and not price.isdigit():
        price = ''
    if isinstance(quality, str) and not quality.isdigit():
        quality = ''

    if (quality=='') and (price==''):
        offer_with_last_information=[price,quality]
        #Offer not defined on Quality, Just Price
        profit_user= -10
        profit_bot= -10
    elif(quality=='') and (price!=''):
        last_quality=find_last_valid_quality(offers)
        offer_with_last_information=[price,last_quality]
        if bot_role== 'supplier':
            # Offer not defined on Quality, Just Price
            profit_bot=price - constrain_bot - last_quality
            profit_user=constrain_user - price + last_quality
        else:
            profit_bot= - price + constrain_bot + last_quality
            profit_user= - constrain_user + price - last_quality

    elif(quality!='') and (price==''):

        last_price=find_last_valid_price(offers)
        offer_with_last_information=[last_price,quality]
        # Offer not defined on Price, Just Quality
        if bot_role== 'supplier':
            profit_bot= last_price - constrain_bot - quality
            profit_user=constrain_user - last_price + quality
        else:
            profit_bot= - last_price + constrain_bot + quality
            profit_user= - constrain_user + last_price - quality
    
    elif(quality!='') and (price!=''):
        offer_with_last_information=[price,quality]
        #Offer properly defined
        if bot_role== 'supplier': 
            profit_bot= price - constrain_bot - quality
            profit_user=constrain_user - price + quality
        else:
            profit_bot= - price + constrain_bot + quality
            profit_user= - constrain_user + price - quality

    offers[tuple(offer_with_last_information)] = profit_bot
    offers_profit_user[tuple(offer_with_last_information)] = profit_user

    if tuple(offer_with_last_information) in offers:
        move_key_to_end(offers, tuple(offer_with_last_information))
    elif tuple(offer_with_last_information) in offers_profit_user:
        move_key_to_end(offers_profit_user, tuple(offer_with_last_information))

    return(profit_bot,offers,offers_profit_user)

def evaluate_profitability(last_offer_profit,all_offers_dict,offers,offers_profit_user,constrain_of_user, user_offers_dictionary): ## FIND HOW TO INCLUDE USER OFFERS AS MAX PROFIT!!

    # Check if the last offer's profitability is worse than or equal to the best stored offer
    if all_offers_dict:
        
        #Just using user offers of to have them as max profit reference. 
       
        max_profit = max(user_offers_dictionary.values())
        best_offers = [k for k, v in user_offers_dictionary.items() if v == max_profit]
        best_offer = best_offers[-1]

        #If both items in the offer were empty take the last best offer. 
        last_entry = list(all_offers_dict.keys())[-1]
        if last_entry == ('', ''):
            #Find the previous best offer
            last_offer_profit=max_profit

        elif last_entry[0] == '' and isinstance(last_entry[1], (int, float)):
            #Find the previous best offer
            last_offer_profit=max_profit

        elif last_entry[1] == '' and isinstance(last_entry[0], (int, float)):
            #Get a combination of a component from the previous best offer
            combined_offer = [[last_entry[0], best_offer[1]]]
            combined_offer_profit=profit_calculator(combined_offer,offers,offers_profit_user,constrain_of_user)[0]
            #calculate profit of combined_offer

            if combined_offer_profit >= max_profit:
                best_offer = (last_entry[0], best_offer[1])
                max_profit = combined_offer_profit
                last_offer_profit = combined_offer_profit
            else:
                last_offer_profit=max_profit
        
        if last_offer_profit <= greedy: #Accepts profits of just a single unit but if we set it to 3 it will be greedy
            if last_offer_profit == max_profit:
                # Find all offers with the max profit
                return('the offer proposed not profitable and there is not previous profitable offer I should come up with a new counter offer',best_offer)  
            elif (last_offer_profit < max_profit) and (max_profit > 0):
                # Find all offers with the max profit
                return("the offer proposed not profitable and is worse than a previous profitable one",best_offer) 
            elif (last_offer_profit < max_profit) and (max_profit <= 0):
                return('the offer proposed not profitable and there is not previous profitable offer I should come up with a new counter offer',best_offer)  
            else:
                return('the offer proposed not profitable and there is not previous profitable offer I should come up with a new counter offer',best_offer)  
        else:
            #Profitable offer
            if last_offer_profit < max_profit:
                # Find all offers with a profit better than the last offer
                return ("Is profitable but there was a better offer previously proposed",best_offer)
            elif last_offer_profit == max_profit:
                #if len(all_offers_dict) <= 0: #not the first couple of offers in the conversation (NOT ACTIVE)

                    # Find all offers with the max profit, which includes the last offer
                 #   return("the offer is good, but too early try to get a better offer",best_offer)
            
                #else:
                    # Find all offers with the max profit, which includes the last offer
                    return("Accept the offer",best_offer)
            else:
                return("Accept the offer", last_entry)
                   
def loop_LLM_Profitable_Prompts(profit_evaluation, user_message, interactions, offers, offers_profit_user,constrain_of_user, user_offers_dictionary):

    count_of_calls_to_LLM=0

    if profit_evaluation[0] == "Accept the offer":
            follow_up_content = 'Accept the offer sent by your negotiation counterpart because the price and quality terms are favourable, thank your counterpart for their understanding but do not disclouse your the exitence of your payoff table. Here is the last from your countepart:'+ user_message
            follow_up_response = ollama.chat(
            model='llama3', 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": follow_up_content}
            ]
            )
            return(extract_content(follow_up_response))

    else:
        while count_of_calls_to_LLM <= 2:
            #print(count_of_calls_to_LLM)
            if (profit_evaluation[0] == 'the offer proposed not profitable and there is not previous profitable offer I should come up with a new counter offer') or (
                    profit_evaluation[0] == "the offer proposed not profitable and is worse than a previous profitable one"):
                    follow_up_content = non_profitable_offer + user_message + follow_up_prompt_2nd + str(interactions)
                    follow_up_response = ollama.chat(
                    model='llama3', 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": follow_up_content}
                    ]
                    )
                    count_of_calls_to_LLM+=1

                    last_item_content= extract_content(follow_up_response)
                    last_offer_bot= reader_of_offers(last_item_content)

                    all_offers_dictionary = profit_calculator(last_offer_bot, offers, offers_profit_user,constrain_of_user)[1]
                    last_offer_bot_profitability = profit_calculator(last_offer_bot, offers, offers_profit_user,constrain_of_user)[0]

                    profit_evaluation= evaluate_profitability(last_offer_bot_profitability,all_offers_dictionary,offers,offers_profit_user,constrain_of_user,user_offers_dictionary)
    
            elif (profit_evaluation[0] =="the offer is good, but too early try to get a better offer") or (profit_evaluation[0] =="Is profitable but there was a better offer previously proposed"):
                follow_up_content = 'You just received a competitive offer try to get a better deal. Increase the price from' + str(profit_evaluation[1][0]) + '€ or decrease the quality from'+ str(profit_evaluation[1][1]) + 'Here is the last from your countepart:'+ user_message
                follow_up_response = ollama.chat(
                model='llama3', 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": follow_up_content}
                ]
                )
                count_of_calls_to_LLM+=1

                last_item_content= extract_content(follow_up_response)
                last_offer_bot= reader_of_offers(last_item_content)

                all_offers_dictionary = profit_calculator(last_offer_bot, offers, offers_profit_user,constrain_of_user)[1]
                last_offer_bot_profitability = profit_calculator(last_offer_bot, offers, offers_profit_user,constrain_of_user)[0]

                profit_evaluation= evaluate_profitability(last_offer_bot_profitability,all_offers_dictionary,offers,offers_profit_user,constrain_of_user,user_offers_dictionary)
            elif profit_evaluation[0] == 'Accept the offer':
                count_of_calls_to_LLM+=3  
                return(extract_content(follow_up_response))
        else:

            return(extract_content(follow_up_response))
        


def main():
    
    # Send the initial message to ollama
    response = ollama.chat(
        model='llama3', 
        messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": initial_prompt}
                    ]
        )


    offers={}
    offers_profit_user={}
    user_offers_dictionary={}
    loops=0 # FIND A WAY TO FIX THE PROBEM WITH THE LOOOOPS IT JUST STARTS AGAIN OUT OF NOWEHRE


    # Print the bot's response
    print(extract_content(response))
    
    # Store conversation history
    interactions = [{"role": "system", "content": response['message']['content']}] 
    interactions=[]
    #Fixed variables
    # Allow user to continue the conversation
    while True:
        user_message = input("Your response (type 'exit' to end): ")

        if user_message.lower() == 'exit':
            print("Negotiation ended.")
            break

        else:
            interactions.append({"role": "user", "content": user_message})
            #print(interactions)
            #Last message sent my user
            last_item_content = interactions[-1]['content']
            
            #Constrain share by the user
            if loops==0:
                constrain_user= reader_of_constrains(last_item_content)
                print(constrain_user)                
                if constrain_user == '[]': 
                    loops+=1
                    print( f"I did not quite understand it. Please clarify your current {context_constrain}.")
                elif isinstance(constrain_user[0], (int, float)):  # Check if constrain is an integer or float
                    loops+=1
                    print(f"Confirming: Is {constrain_user[0]} the correct {context_constrain}?, if it is correct, please enter {constrain_user[0]} again in the chat bellow, otherwise enter your current {context_constrain} at the quality level of 0")
                else:
                    loops+=1
                    print( f"I did not quite understand it. Please clarify your current {context_constrain}.")
            elif loops ==1:
                constrain_user= reader_of_constrains(last_item_content)
                #print(constrain_user)
                if isinstance(constrain_user[0], (int, float)):  # Check if constrain is an integer or float
                    print("Thanks, for confirming this information with me. What is the ideal/desired combination of Price and Quality you aim to get out of this negotiation?")
                    loops+=1
                    if not (10 >= constrain_user[0] >= 8 or 3 >= constrain_user[0] >= 1):
                        # If the value is outside the specified ranges, draw randomly
                        final_constrain = randomly_drawn
                    else:
                        final_constrain=constrain_user[0]
                else:
                    #RANDOMLY DRAWN CONSTRAIN FROM UNIFORM DISTRIBUTION
                    print("Thanks, for confirming this information with me. What is the ideal/desired combination of Price and Quality you aim to get out of this negotiation?")
                    final_constrain=randomly_drawn
                    loops+=1
            else:
                #Read user message
                #Offer made by the user via chat
                last_offer_user= reader_of_offers(last_item_content)
                user_offers_dictionary =  profit_calculator(last_offer_user,offers=user_offers_dictionary,offers_profit_user=offers_profit_user,constrain_of_user=final_constrain)[1]
                #print("Last USER_OFFER",last_offer_user)
                all_offers_dictionary = profit_calculator(last_offer_user,offers,offers_profit_user,final_constrain)[1]
                #print("All Offers", all_offers_dictionary)
               # print("User Offers", user_offers_dictionary)
                last_offer_profitability_for_bot = profit_calculator(last_offer_user,offers,offers_profit_user,final_constrain)[0]
                rule_based_profit_evaluation= evaluate_profitability(last_offer_profitability_for_bot,all_offers_dictionary,offers,offers_profit_user,final_constrain, user_offers_dictionary)
                
                bot_response=loop_LLM_Profitable_Prompts(rule_based_profit_evaluation, user_message, interactions, offers, offers_profit_user,final_constrain, user_offers_dictionary)
                interactions.append({"role": "system", "content": bot_response})
                print(bot_response)

if __name__ == "__main__":
    main()  
