import json
import argparse
import random
from collections.abc import Iterable
from collections import Counter

def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

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

def generate_pronunciation_key(word, katakana):
    return list(map(lambda x: katakana.get(x, x), word))

def select_word(words):
    return random.choice(words)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'wordfiles',
        action='append',
        nargs='+',
        type=str
    )
    args = parser.parse_args()

    

    words = load_words(flatten(args.wordfiles))
    wordlist = list(words.keys())
    katakana = load_katakana()
    
    pronunciations = \
        {x: generate_pronunciation_key(x, katakana) 
          for x in words.keys()}


    count = 0
    correct = 0

    most_incorrect = Counter()
    most_correct = Counter() 
    try:
        while True:
            word = select_word(wordlist)
            print(f'What is: {word} ?')
            guess = input("-> ")
            if guess.lower().replace(' ', '') == words[word].lower().replace(' ',''):
                correct += 1
                most_correct[word] += 1
                print(f'Well done, it was "{guess}" !')
            else:
                pronunciation = pronunciations[word]
                most_incorrect[word] += 1
                print(f'Oops, it wasn\'t "{guess}')
                print(f'It\'s pronounced like "{pronunciation}"')
                print(f'The answer is {words[word]}')
            print()
            count += 1
            if count % 20 == 0:
                print(f'success rate {correct/float(count)}')            
    except KeyboardInterrupt:
         print(f"Done, {count} attempts, {correct} correct")
         print(most_correct.most_common(2))

if __name__ == '__main__':
    main()

