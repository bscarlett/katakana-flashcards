#!/usr/bin/env python3

#stdlib imports
import json
import argparse
import random
from collections.abc import Iterable
from collections import Counter
from subprocess import call

#3rd party imports
import urwid

def flatten(iterable):
    for item in iterable:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item

def load_words(filenames):
    '''Return a dict of all the words to flash'''
    items = {}
    for filename in filenames:
        with open(filename) as f:
           items.update(json.load(f))
    return items

def load_katakana():
    with open('katakana.json') as f:
        return json.load(f)

#TODO handle digraphs
def generate_pronunciation_key(word, katakana):
    return list(map(lambda x: katakana.get(x, x), word))

#TODO spaced repetition of incorrect answers
def select_word(words):
    return random.choice(words)

def handle_global_command(flashcards, key):
    if key == 'meta q':
       raise urwid.ExitMainLoop
    if key == 'enter':
       flashcards.next_card()
       return True

#TODO collect and show statistics
#TODO help mode to show katakana table
#TODO hints mode show category
#TODO hints mode show specific hint
class Flashcards(object):
    def __init__(self, args):
        self.words = load_words(flatten(args.wordfiles))

        self.wordlist = list(self.words.keys())
        self.katakana = load_katakana()

        self.editor = urwid.Edit("", align="center")
        self.question = select_word(self.wordlist)
        self.header = urwid.Text(self.question, align="center")
        self.footer = urwid.Text("", align="center")
        self.current_card = urwid.Filler(
            urwid.Padding(
                urwid.LineBox(
                    urwid.Frame(
                        urwid.Filler(self.editor),
                        header=self.header,
                        footer=self.footer
                    )
                ),
                align='center',
                width=('relative', 40),
                min_width=20
            ),
            valign='middle',
            height=('relative', 40),
            min_height=5
        )


    def verify_answer(self):
        value = self.editor.get_edit_text().lower().replace(" ","")
        result = value == self.words[self.question].lower().replace(" ","")
        return result

    def next_card(self):
        previous_correct = self.verify_answer()
        if previous_correct:
            footer_text = f"Correct, {self.question} is {self.words[self.question]}"
        else:
            pkey = generate_pronunciation_key(self.question, self.katakana)
            footer_text = f"Incorrect, {self.question} is {self.words[self.question]}\n{pkey}"
        self.question = select_word(self.wordlist)
        self.editor.set_edit_text("")
        self.header.set_text(self.question)
        self.footer.set_text(footer_text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'wordfiles',
        action='append',
        nargs='+',
        type=str
    )
    args = parser.parse_args()

    flashcards = Flashcards(args)
    loop = urwid.MainLoop(flashcards.current_card, unhandled_input=lambda x: handle_global_command(flashcards, x) )
    loop.run()

    #FIXME: call to clear the shell, couldn't get urwid to do it
    call("clear", shell=True)

if __name__ == '__main__':
    main()

