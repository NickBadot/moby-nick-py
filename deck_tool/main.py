from tkinter import *
from tkinter import scrolledtext

from deck_tool.deck_tools import *


def main():
    # initialise the deck
    deck = create_mutation_deck()
    deck.shuffle()

    # open the window
    window = Tk()
    window.title("Badot's Bedazzling Deck Tool ")
    window.geometry('550x350')

    window_text = scrolledtext.ScrolledText(width=65, height=15)
    window_text.grid(column=0, row=0)
    window_text.insert(INSERT, "Welcome to Badot's Bedazzling Deck Tool, choose a Deck to play with")

    # Button Methods
    def draw_clicked():
        window_text.delete(1.0, END)
        if deck.deck_size() == 0:
            window_text.insert(INSERT, "No More cards to draw")
        else:
            card = deck.draw_card()
            window_text.insert(INSERT,
                               "You have drawn..." + card.name + "\n\n\n" + card.description + "\n\n\n" +
                               str(deck.deck_size()) + " cards remain mortal")

    def mutation_clicked():
        window_text.delete(1.0, END)
        window_text.insert(INSERT, deck.name + "\n" + deck.description)
        draw_card_button = Button(window, text="Draw Card", command=draw_clicked)
        draw_card_button.grid(column=0, row=2)

    deck_of_mutations_button = Button(window, text="Deck of Many Mutations", command=mutation_clicked)
    deck_of_mutations_button.grid(column=0, row=1)
    window.mainloop()

    # card = deck.draw_card()
    # print(card.display())


if __name__ == "__main__":
    main()
