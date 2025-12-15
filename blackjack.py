import pygame
import random
import os


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


def get_card_image_path(rank, suit):
    """
    Convert card rank and suit to the filename of the corresponding card image.
    e.g., ('A', 'Hearts') -> 'ace_of_hearts.png'
    """
    rank_to_name = {
        '2': '2', '3': '3', '4': '4', '5': '5', '6': '6',
        '7': '7', '8': '8', '9': '9', '10': '10',
        'J': 'jack', 'Q': 'queen', 'K': 'king', 'A': 'ace'
    }
    suit_to_name = {
        'Hearts': 'hearts',
        'Diamonds': 'diamonds',
        'Clubs': 'clubs',
        'Spades': 'spades'
    }

    rank_name = rank_to_name.get(rank, rank.lower())
    suit_name = suit_to_name.get(suit, suit.lower())
    filename = f"{rank_name}_of_{suit_name}.png"
    return os.path.join('images', 'PNG-cards-1.3', filename)


def load_card_images(card_list, size=(80, 120)):
    """
    Load pygame surfaces for a list of cards.
    Returns a list of surfaces corresponding to each card.
    """
    surfaces = []
    for rank, suit in card_list:
        path = get_card_image_path(rank, suit)
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            surfaces.append(img)
        except:
            # Fallback: create a placeholder surface if image not found
            placeholder = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(placeholder, (200, 200, 200),
                             (0, 0, size[0], size[1]))
            pygame.draw.rect(placeholder, (100, 100, 100),
                             (0, 0, size[0], size[1]), 2)
            surfaces.append(placeholder)
    return surfaces


def load_card_back_image(size=(80, 120)):
    """
    Load the card back image (for hidden cards).
    """
    try:
        img = pygame.image.load(os.path.join(
            'images', 'PNG-cards-1.3', 'red_joker.png')).convert_alpha()
        img = pygame.transform.scale(img, size)
        return img
    except:
        # Fallback: create a placeholder for card back
        placeholder = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(placeholder, (200, 0, 0), (0, 0, size[0], size[1]))
        pygame.draw.rect(placeholder, (100, 0, 0), (0, 0, size[0], size[1]), 2)
        return placeholder
