"""
Offer class for the V5_garrido_negotiations system.
"""

import time
from typing import Any, Union

from constants import C

ACCEPT = 'accept'
NOT_PROFITABLE = 'not_profitable'
OFFER_QUALITY = 'offer_quality'
OFFER_PRICE = 'offer_price'
NOT_OFFER = 'not_offer'
INVALID_OFFER = 'invalid_offer'


class Offer(dict):
    def __init__(self,
                 idx: int = -1,
                 price: int = None,
                 quality: int = None,
                 stamp: int = None,
                 from_chat: bool = False,
                 enhanced: str = None,
                 profit_bot: int = None,
                 profit_user: int = None,
                 test: Any = None):
        stamp = stamp or int(time.time())
        dict.__init__(self, idx=idx, price=price, quality=quality,
                      stamp=stamp, from_chat=from_chat, enhanced=enhanced,
                      profit_bot=profit_bot, profit_user=profit_user,
                      test=test)
        self.idx = idx
        self.price = price
        self.quality = quality
        self.stamp = stamp
        self.from_chat = from_chat
        self.enhanced = enhanced
        self.profit_bot = profit_bot
        self.profit_user = profit_user

    def __getattr__(self, attr):
        return self.get(attr)

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    @property
    def specifics(self) -> str:
        return f"P+Q = {str(self.price):4} + {str(self.quality):4} ; " \
               f"PROF = {str(self.profit_bot):3} + {str(self.profit_user):3} ;"

    @property
    def is_valid(self) -> bool:
        return self.is_complete and \
               self.price_in_range and self.quality_in_range

    @property
    def is_complete(self) -> bool:
        return None not in (self.price, self.quality)

    @property
    def price_in_range(self) -> bool:
        return self.price in C.PRICE_RANGE

    @property
    def quality_in_range(self) -> bool:
        return self.quality in C.QUALITY_RANGE

    def enhance(self, offer_list: 'OfferList', idx: int = None):
        """ Adds missing price or quality from last data
        """
        if self.price is None:
            self.price = offer_list.last_valid_price(idx)
            self.enhanced = 'price'
        if self.quality is None:
            self.quality = offer_list.last_valid_quality(idx)
            if self.enhanced is not None:
                self.enhanced += ' '
            self.enhanced = 'quality'

    def profits(self, bot_role: str, constraint_user: int, constraint_bot: int):
        """ This calculates the profits for the user and the bot """
        if not self.is_valid or None in (constraint_user, constraint_bot):
            self.profit_bot = -10
            self.profit_user = -10
            return

        args_bot = (self.price, self.quality, constraint_bot)
        args_user = (self.price, self.quality, constraint_user)

        if bot_role == C.ROLE_SUPPLIER:
            self.profit_bot = self.profit_supplier(*args_bot)
            self.profit_user = self.profit_buyer(*args_user)
        else:
            self.profit_bot = self.profit_buyer(*args_bot)
            self.profit_user = self.profit_supplier(*args_user)

    def evaluate(self, greedy: int) -> str:
        if self.profit_bot >= greedy:
            return ACCEPT
        elif self.is_valid:
            return NOT_PROFITABLE
        elif self.price is None and self.quality_in_range:
            return OFFER_QUALITY
        elif self.quality is None and self.price_in_range:
            return OFFER_PRICE
        elif self.price is not None and not self.price_in_range:
            return INVALID_OFFER
        elif self.quality is not None and not self.quality_in_range:
            return INVALID_OFFER
        else:
            return NOT_OFFER

    @staticmethod
    def profit_supplier(price: int, quality: int, production_cost: int) -> int:
        return price - production_cost - quality

    @staticmethod
    def profit_buyer(price: int, quality: int, market_price: int) -> int:
        return market_price - price + quality


class OfferList(list):
    def __init__(self, *args):
        list.__init__(self, *args)
        # Make sure this is always sorted on stamp
        self.sort(key=lambda o: o.stamp)

    def last_valid_price(self, idx: int = None) -> Union[int, float]:
        # Sort on latest timestamp
        for offer in sorted(self, key=lambda o: -o.stamp):
            # Ignore offers from other players
            if idx is not None and offer.idx != idx:
                continue
            if offer.price is not None:
                return offer.price
        return 5

    def last_valid_quality(self, idx: int = None) -> int:
        # Sort on latest timestamp
        for offer in sorted(self, key=lambda o: -o.stamp):
            # Ignore offers from other players
            if idx is not None and offer.idx != idx:
                continue
            if offer.quality is not None:
                return offer.quality
        return 2

    @property
    def max_profit(self) -> int:
        if len(self) == 0:
            return 0
        # Only check for user offers
        return max([offer.profit_bot for offer in self if offer.idx != -1])

    @property
    def min_profit(self) -> int:
        # Only check for user offers
        return min([offer.profit_bot for offer in self if offer.idx != -1])
