"""
Prompt manager for the V5_garrido_negotiations system.
"""

import os
from typing import Dict

from constants import C, Config


def from_file(base_path: str, file_path: str) -> str:
    with open(os.path.join(base_path, file_path), 'r') as f:
        content = f.read()
    return content.strip() + '\n'


def system_final_prompt(config: Config):
    bot_role = config.get('bot_role')

    before_constraint = PROMPTS[bot_role]['before_constraint']
    bot_constraint = config.get('constraint_bot')
    after_constraint = PROMPTS[bot_role]['after_constraint_before_price']

    f = 1 - 2 * (bot_role == C.ROLE_BUYER)
    constraints = str([f * (i - bot_constraint) for i in C.PRICE_RANGE])

    after_price = PROMPTS[bot_role]['after_price']

    return (before_constraint +
            f"{bot_constraint}€" +
            after_constraint +
            constraints +
            after_price)


def empty_offer_prompt(config: Config,
                       user_message: str,
                       offers_pareto_efficient: str,
                       interactions: str) -> str:
    bot_role = config.get('bot_role')
    prompts = PROMPTS[bot_role]
    return (prompts['follow_up_prompt_without_offer'] +
            user_message + ' ' +
            prompts['non_profitable_offer_or_deal'] +
            offers_pareto_efficient + '\n' +
            prompts['follow_up_conversation'] +
            interactions)


def offer_without_quality_prompt(config: Config,
                                 user_message: str,
                                 offers_pareto_efficient: str,
                                 interactions: str) -> str:
    bot_role = config.get('bot_role')
    prompts = PROMPTS[bot_role]
    return (prompts['follow_up_prompt_without_quality'] +
            user_message + ' ' +
            prompts['non_quality_offer'] +
            offers_pareto_efficient + '\n' +
            prompts['follow_up_conversation'] +
            interactions)


def offer_without_price_prompt(config: Config,
                               user_message: str,
                               offers_pareto_efficient: str,
                               interactions: str) -> str:
    bot_role = config.get('bot_role')
    prompts = PROMPTS[bot_role]
    return (prompts['follow_up_prompt_without_price'] +
            user_message + ' ' +
            prompts['non_price_offer'] +
            offers_pareto_efficient + '\n' +
            prompts['follow_up_conversation'] +
            interactions)


def not_profitable_prompt(config: Config,
                          user_message: str,
                          offers_pareto_efficient: str,
                          interactions: str) -> str:
    bot_role = config.get('bot_role')
    prompts = PROMPTS[bot_role]
    return (prompts['follow_up_prompt_2nd'] +
            user_message + ' ' +
            prompts['non_profitable_offer'] +
            offers_pareto_efficient + '\n' +
            prompts['follow_up_conversation'] +
            interactions)


def offer_invalid(config: Config, user_message: str) -> str:
    bot_role = config.get('bot_role')
    prompts = PROMPTS[bot_role]
    return (prompts['follow_up_invalid_offer'] +
            user_message + ' ' +
            prompts['invalid_offer_reminder'])


def role_prompts(base: str) -> Dict[str, str]:
    return {
        'before_constraint': from_file(base, 'system/before_constraint.txt'),
        'after_constraint_before_price': from_file(
            base, 'system/after_constraint_before_price.txt'),
        'after_price': from_file(base, 'system/after_price.txt'),
        'initial': from_file(base, 'intro_user.txt'),

        'follow_up_prompt_2nd': from_file(base, 'follow_up_user_message.txt'),
        'follow_up_prompt_without_offer': from_file(
            base, 'follow_up_user_message_without_offer.txt'),
        'follow_up_prompt_without_price': from_file(
            base, 'follow_up_user_message_without_price.txt'),
        'follow_up_prompt_without_quality': from_file(
            base, 'follow_up_user_message_without_quality.txt'),
        'non_profitable_offer': from_file(
            base, 'non_profitable_Send_Pareto_Efficient_Offer.txt'),
        'non_profitable_offer_or_deal': from_file(
            base, 'Send_Pareto_Efficient_or_Instructions.txt'),
        'follow_up_conversation': from_file(
            base, 'follow_up_conversation_history.txt'),
        'non_quality_offer': from_file(
            base, 'Not_Quality_Send_Pareto_Efficient_Offer.txt'),
        'follow_up_invalid_offer': from_file(
            base, 'follow_up_user_message_invalid_offer.txt'),
        'invalid_offer_reminder': from_file(
            base, 'invalid_offer_reminder.txt'),
        'non_price_offer': from_file(
            base, 'Not_Price_Send_Pareto_Efficient_Offer.txt'),
    }


PROMPTS = {
    'first_message_PC': "Hi! I'm excited to start our negotiation. As we begin, I'd like to get a sense of your needs and constraints. Can you share with me your Base Production Cost?",
    'first_message_MP': "Hi! I'm excited to start our negotiation. As we begin, I'd like to get a sense of your needs and constraints. Can you share with me your Base Market Selling Price to Consumer?",
    'offer_string': f"Price of %s€ and quality of %s",
    'constraints': 'Here is the negotiator message you need to read: ',
    'context_constraint': {
        C.ROLE_BUYER: 'Base Production Cost (PC)',
        C.ROLE_SUPPLIER: 'Base Market Selling Price to Consumer (MP)',
    },
    'constraint_clarify':
        'I did not quite understand. '
        'Please clarify your current %s at the quality level of 0.',
    'constraint_confirm':
        'Confirming: Is %s the correct %s?\n'
        'If it is correct, please ONLY enter %s again in the chat bellow.\n'
        'Otherwise enter your current %s at the quality level of 0.',
    'constraint_offer':
        'I am not ready to respond to your offer yet. '
        'Please clarify your current %s at the quality level of 0 (in the chat bellow).',
    'constraint_persist_final_buyer':
        'My apologies for persisting.\n'
        'Note: My data regarding the normal range of Base Market Selling Prices to Consumers has values between 8 and 10. Thus, I will assume your actual value is 10. \n'
        'What combination of Price and Quality do you have in mind '
        'to purchase a 10kg pellet bag?',
    'constraint_persist_final_supplier':
        'My apologies for persisting.\n'
        'Note: My data regarding the normal range of Base Production Cost has values between 1 and 3. Thus, I will assume your actual value is 1. \n'
        'What combination of Price and Quality do you have in mind '
        'to sell me a 10kg pellet bag?',
    'constraint_final_buyer':
        'Thanks, for confirming this information with me.\n'
        'What combination of Price and Quality do you have in mind '
        'to purchase a 10kg pellet bag?',
    'constraint_final_supplier':
        'Thanks, for confirming this information with me.\n'
        'What combination of Price and Quality do you have in mind '
        'to sell me a 10kg pellet bag?',

    'understanding_offer':
        'Here is the negotiator message you need to read: ',

    'accept_from_chat': 'Accept the offer sent by your negotiation counterpart '
              'because the price and quality terms are favourable, '
              'thank your counterpart for their understanding but do not '
              'disclose the existence of your payoff table. '
              'Also, Ask your counterpart to please click the CONFIRM button in the interface, which can be found bellow the SEND button.'
              '(Maximum 30 words and one paragraph) '
              'Here is the last message from your counterpart: ',
    'accept_from_interface': 'Accept the offer sent by your negotiation counterpart '
                'because the price and quality terms are favourable, '
                'thank your counterpart for their understanding but do not '
                'disclose the existence of your payoff table. '
                '(Maximum 30 words and one paragraph) '
                'Here is the last message from your counterpart: ',

    C.ROLE_BUYER: role_prompts('./prompts/buyer/'),
    C.ROLE_SUPPLIER: role_prompts('./prompts/supplier/'),
}
