#!/usr/bin/env python3

#stdlib imports
import json
import argparse
import random
from collections.abc import Iterable
from collections import Counter, deque
from subprocess import call

#3rd party imports
import urwid

def count(predicate, iterable):
    return sum(1 for item in iterable if predicate(item))

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

def select_word(words, recently_incorrect, last_word):
    # 75% of the time, if there are recently incorrect answers, choose from those.
    if random.random() <= 0.75 and len(recently_incorrect) > 0:
       word = random.choice(recently_incorrect)
    else:
       word = random.choice(words)

    # Don't choose the same word again
    if word == last_word:
        return select_word(words, recently_incorrect, last_word)
    else:
        return word

def handle_global_command(flashcards, key):
    if key == 'meta q':
       raise urwid.ExitMainLoop
    if key == 'enter':
       flashcards.next_card()
       return True


class Statistics(object):
    def __init__(self):
        self.total_incorrect = 0
        self.total_correct = 0
        self.recent_results = deque(maxlen=15)
        self.widget = urwid.Text("hello.", align='right')

    def record(self, word, correct):
        if correct:
            self.total_correct += 1
        else:
            self.total_incorrect += 1
        self.recent_results.append((word, correct))
        self.set_widget_text()

    def get_recent_incorrect_words(self):
        return [x[0] for x in self.recent_results if not x[1]]

    def get_recent_success_rate(self):
        success_rate = count(lambda x: x[1], self.recent_results) / float(len(self.recent_results))
        return f"{success_rate:.2f}"

    def get_total_success_rate(self):
        success_rate = self.total_correct / float(self.total_correct + self.total_incorrect)
        return f"{success_rate:.2f}"

    def set_widget_text(self):
        self.widget.set_text(f"Total: {self.get_total_success_rate()}, Recently: {self.get_recent_success_rate()}")


#TODO help mode to show katakana table
#TODO hints mode show category
#TODO hints mode show specific hint
class Flashcards(object):
    def __init__(self, args):
        # Words
        self.words = load_words(flatten(args.wordfiles))
        self.wordlist = list(self.words.keys())
        self.katakana = load_katakana()

        # Statistics
        self.stats = Statistics()

        # UI / State
        self.editor = urwid.Edit("", align="center")
        self.question = select_word(self.wordlist, self.stats.get_recent_incorrect_words(), None)
        self.header = urwid.Text(self.question, align="center")
        self.footer = urwid.Text("", align="center")
        self.stats.widget
        self.current_card = urwid.Overlay(
            urwid.LineBox(
                urwid.Frame(
                    urwid.Filler(self.editor),
                    header=self.header,
                    footer=self.footer
                )
            ),
            urwid.Filler(self.stats.widget, valign="bottom"),
            align='center',
            width=('relative', 40),
            min_width=20,
            valign='middle',
            height=('relative', 40),
            min_height=5
        )


    def verify_answer(self):
        value = self.editor.get_edit_text().lower().replace(" ","")
        result = value == self.words[self.question].lower().replace(" ","")
        self.stats.record(self.question, result)
        return result

    def next_card(self):
        previous_correct = self.verify_answer()
        if previous_correct:
            footer_text = f"Correct, {self.question} is {self.words[self.question]}"
        else:
            pkey = generate_pronunciation_key(self.question, self.katakana)
            footer_text = f"Incorrect, {self.question} is {self.words[self.question]}\n{pkey}"
        self.question = select_word(self.wordlist, self.stats.get_recent_incorrect_words(), self.question)
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

