# TODO: Maybe factor out the common stuff.

import random
from typing import Dict, List, Mapping, Set, Tuple
import argparse
import sys

DICTIONARY_FILE = "/usr/share/dict/american-english"
WORDLE_LEN = 5

CHARACTERS = [chr(i) for i in range(ord("a"), ord("z") + 1)]
FEEDBACK_CHARS = ("x", "v", "o")

def is_valid_word(word: str) -> bool:
    return len(word) == WORDLE_LEN


def is_alpha(c: str) -> bool:
    assert len(c) == 1
    return ord("a") <= ord(c) <= ord("z")


def initial_word_list() -> List[str]:
    words = []
    with open(DICTIONARY_FILE, "r") as f:
        for line in f:
            word = "".join(c for c in line.strip().lower() if is_alpha(c))
            if is_valid_word(word):
                words.append(word)
    return sorted(set(words))


class GameState:

    def __init__(self, word_list, quiet, word=None):
        self.word_list = word_list
        self.word = word or self.select_random_word()
        self.quiet = quiet

    def select_random_word(self):
        return random.choice(self.word_list)

    def print_word(self):
        print(self.word)

    def is_valid_candidate(self, word) -> bool:
        if not is_valid_word(word):
            return False
        return all(is_alpha(c) for c in word)

    def get_feedback(self, candidate: str) -> str:
        feedback = ""
        for candidate_c, target_c in zip(candidate, self.word):
            if candidate_c == target_c:
                feedback += "o"
            elif candidate_c in self.word:
                feedback += "v"
            else:
                feedback += "x"
        return feedback

    def print_feedback(self, word):
        feedback = self.get_feedback(word)
        print(feedback)
        if self.quiet and feedback == "o" * WORDLE_LEN:
            sys.exit(1)


def print_help():
    print(f"Type a {WORDLE_LEN} letter long word.")
    print(f"You will be given a {WORDLE_LEN} letter-long string in return.")
    print("In this string, each letter indicates the following:")
    print("- X to indicate a missed letter")
    print("- V to indicate the letter is in the word but in the incorrect place")
    print("- O to indicate a correctly placed letter")
    print()
    print("If the word is invalid, \"n/a\" is printed.")
    print("Type help to see this message again.")
    print("Type giveup to reveal the hidden word.")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Play Wordle.")
    parser.add_argument("word", type=str,
                        nargs="?",
                        default=None,
                        help="The hidden word. Used for debug.")
    parser.add_argument("-q", "--quiet",
                        action="store_true",
                        help="If set, outputs much less. Suitable for machine parsing.")
    args = parser.parse_args()
    prompt = "> "
    if args.quiet:
        prompt = ""
    word_list = initial_word_list()

    game_state = GameState(word_list, args.quiet, args.word)

    while True:
        try:
            cmd = input(prompt).strip().lower()
        except EOFError:
            continue
        if cmd == "help":
            print_help()
        elif cmd in ("quit", "exit"):
            break
        elif cmd == "giveup":
            game_state.print_word()
        elif game_state.is_valid_candidate(cmd):
            game_state.print_feedback(cmd)
        else:
            print_help()
