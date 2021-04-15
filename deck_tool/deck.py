import random


class Card:

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def display(self):
        return "You have drawn %s\nDescription:\n%s" % (self.name, self.description)


class Deck:

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.cards = []

    def add_card(self, card):
        self.cards.append(card)

    def deck_size(self):
        return len(self.cards)

    def shuffle(self):
        random.shuffle(self.cards)

    def draw_card(self):
        return self.cards.pop()
