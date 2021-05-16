from deck_tool.deck import *
from deck_tool.deck_templates.deck_of_mutations_template import *


def create_deck(name, description, cards):
    deck = Deck(name, description)
    deck_cards = get_list_of_cards(cards)
    for card in deck_cards:
        deck.add_card(card)
    return deck


def get_list_of_cards(cards):
    card_list = []
    for key, value in cards.items():
        card_list.append(Card(key, value))
    return card_list


def create_mutation_deck():
    return create_deck(DECK_OF_MUTATIONS_NAME, DECK_OF_MUTATIONS_DESCR, DECK_OF_MUTATIONS_CARDS)