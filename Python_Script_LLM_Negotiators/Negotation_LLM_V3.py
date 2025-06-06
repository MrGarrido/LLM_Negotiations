import ollama
import re

"""
This bot utilizes an LLM for interpreting text inputs and a set of rules (IF-ELSE) to evaluate the profitability
of offers based on predefined criteria such as price and quality. The bot's functionality is segmented into various
functions each handling specific tasks:

Functions:
    extract_content(response: dict) -> str:
        Extracts and returns the content enclosed within quotation marks from a provided message dictionary.
        If no quotations are found, returns the entire content string.

    reader_of_offers(message: str) -> list:
        LLM that parses a user text message to extract negotiation terms enclosed within brackets. Simple task to read the message 
        from a negotiator and output the price and quality that the negotiator is proposing in the following format: 
        [Price in Euros, Quality] like [6€,1] or [,3] or [7€,]
    

    profit_calculator(offer: list, offers: dict) -> tuple:
        Calculates the profitability of a given offer based on the price, quality, and predefined costs. Updates and returns
        the offers dictionary with the profitability score for each offer.

    evaluate_profitability(last_offer_profit: float, all_offers_dict: dict) -> tuple:
        Compares the profitability of the most recent offer against all previously stored offers to determine the best
        strategic response based on the negotiation goals.

    main():
        Manages the negotiation process by continuously interacting with a user, processing their messages to extract offers,
        evaluating their profitability, and responding accordingly to maximize negotiation outcomes.

Example usage:
    Running this script will initiate a user-interactive session where negotiation terms can be sent, processed, and
    evaluated in real-time. The session continues until 'exit' is input by the user.

    Try prompts as:
    - Hi! I am looking for any price agreement bellow the market price of 5€ so that I can also make a profit. I was also hoping to get a quality of at least 2. How does that sound?
    - I would like to agree on a price of 5 and a quality of 1, do we have a deal?   
   
"""


system_prompt = open('./V1.5_Prompts/system_prompt_with_payoffs_and_rules.txt', 'r').read()
initial_prompt = open('./V1.5_Prompts/intro_user_prompt.txt', 'r').read()
follow_up_prompt_1st = open('./V1.5_Prompts/follow_up_user_prompt_first_part.txt', 'r').read()
follow_up_prompt_2nd = open('./V1.5_Prompts/follow_up_user_prompt_intermediate.txt', 'r').read()
Reformulate_price_below_production_cost= open('./V2_Reviewing_potential_offers/Reformulate_price.txt', 'r').read()
Reformulate_price_and_quality_not_profitable=open('./V2_Reviewing_potential_offers/Reformulate_both_price_and_Quality.txt', 'r').read()
accept_deal_prompt= 'n'
non_profitable_offer = open('./V2_Reviewing_potential_offers/V2_User_profitability_offer/non_profitable_increaseP_DecreaseQ.txt', 'r').read()

greedy = 3 #use 0 for a generous negotiatior that just looks for a profit higher than 0

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
                price = int(price)
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

def profit_calculator(offer,offers):
    price= offer[0][0]
    quality=offer[0][1]
    production_cost=2

    if isinstance(price, str) and not price.isdigit():
        price = ''
    if isinstance(quality, str) and not quality.isdigit():
        quality = ''

    if (quality=='') and (price==''):
        #Offer not defined on Quality, Just Price
        profit=-(production_cost +10)
    
    elif(quality=='') and (price!=''):
        last_quality=find_last_valid_quality(offers)
        # Offer not defined on Quality, Just Price
        profit=price-production_cost-last_quality

    elif(quality!='') and (price==''):
        # Offer not defined on Price, Just Quality
        profit=-(quality+production_cost)
    
    elif(quality!='') and (price!=''):
        #Offer properly defined
        profit=price-production_cost-quality
    
    offers[tuple(offer[0])] = profit

    return(profit,offers)

def evaluate_profitability(last_offer_profit,all_offers_dict):

    # Check if the last offer's profitability is worse than or equal to the best stored offer
    if all_offers_dict:
        max_profit = max(all_offers_dict.values())
        best_offers = [k for k, v in all_offers_dict.items() if v == max_profit]
        best_offer = best_offers[-1]

        #If both items in the offer were empty take the last best offer. 
        last_entry = list(all_offers_dict.keys())[-1]
        if last_entry == ('', ''):
            last_offer_profit=max_profit

        elif last_entry[0] == '' and isinstance(last_entry[1], (int, float)):
            last_offer_profit=max_profit

        elif last_entry[1] == '' and isinstance(last_entry[0], (int, float)):
            best_offer = (last_entry[0], best_offer[1])
        
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
            #Profitable offer
            if last_offer_profit < max_profit:
                # Find all offers with a profit better than the last offer
                return ("Is profitable but there was a better offer previously proposed",best_offer)
            elif last_offer_profit == max_profit:
                if len(all_offers_dict) <= 2: #not the first two offers of the conversation

                    # Find all offers with the max profit, which includes the last offer
                    return("the offer is good, but too early try to get a better offer",best_offer)
                
                else:
                    # Find all offers with the max profit, which includes the last offer
                    return("Accept the offer",best_offer)

def loop_LLM_Profitable_Prompts(profit_evaluation, user_message, interactions, offers):

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
        if count_of_calls_to_LLM<=5:

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
                    last_offer_user= reader_of_offers(last_item_content)

                    #print(last_offer_user)

                    all_offers_user_dictionary = profit_calculator(last_offer_user,offers)[1]
                    last_offer_user_profitability = profit_calculator(last_offer_user,offers)[0]

                    profit_evaluation= evaluate_profitability(last_offer_user_profitability,all_offers_user_dictionary)
                    
            elif (profit_evaluation[0] =="the offer is good, but too early try to get a better offer") or ("Is profitable but there was a better offer previously proposed"):
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
                last_offer_user= reader_of_offers(last_item_content)

                #print(last_offer_user)

                all_offers_user_dictionary = profit_calculator(last_offer_user,offers)[1]
                last_offer_user_profitability = profit_calculator(last_offer_user,offers)[0]

                profit_evaluation= evaluate_profitability(last_offer_user_profitability,all_offers_user_dictionary)

            elif profit_evaluation[0] == "Accept the offer":
                count_of_calls_to_LLM+=5     
            
        else:
            return(extract_content(follow_up_response))
        
        return(extract_content(follow_up_response))


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
    print(response['message']['content'])
    
    # Store conversation history
    interactions = [{"role": "system", "content": response['message']['content']}]

    offers={}
    # Allow user to continue the conversation
    while True:
        user_message = input("Your response (type 'exit' to end): ")
        if user_message.lower() == 'exit':
            print("Negotiation ended.")
            break
        interactions.append({"role": "user", "content": user_message})
        #Last message sent my user
        last_item_content = interactions[-1]['content']
        #Offer made by the user via chat
        last_offer_user= reader_of_offers(last_item_content)
        print(last_offer_user)
        all_offers_user_dictionary = profit_calculator(last_offer_user,offers)[1]
        last_offer_user_profitability = profit_calculator(last_offer_user,offers)[0]

        #evaluating the profitability of that offer:
        print(evaluate_profitability(last_offer_user_profitability,all_offers_user_dictionary))
        print(all_offers_user_dictionary)

        rule_based_profit_evaluation= evaluate_profitability(last_offer_user_profitability,all_offers_user_dictionary)

        print(loop_LLM_Profitable_Prompts(rule_based_profit_evaluation, user_message, interactions, offers))
        
        

if __name__ == "__main__":
    main()
