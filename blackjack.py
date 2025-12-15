import pygame
import random


class Cards:
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
              'J': 10, 'Q': 10, 'K': 10, 'A': 11}

    def __init__(self):
        self.deck = [(rank, suit)
                     for suit in self.SUITS for rank in self.RANKS]
        random.shuffle(self.deck)

    def deal_card(self):
        return self.deck.pop() if self.deck else None

    def calculate_hand_value(self, hand):
        value = sum(self.VALUES[card[0]] for card in hand)
        aces = sum(1 for card in hand if card[0] == 'A')
        while value > 21 and aces:
            value -= 10
            aces -= 1
        return value
