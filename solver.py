# Load dictionary into memory
# analyze frequency of letters
# Find word that maximizes information

from typing import Dict, List, Mapping, Set, Tuple
import collections
import argparse

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


# Matrix M counts the number of words in the corpus with character c at position n.
# Matrix N counts the number of words in the corpus with charcter c but _not_ at position n.
# Mathematically, M_{n,c} represents the number of words with character c at position n.
# And, N_{n,c} represents the number of words with character c anywhere but position n.
def get_matrices(word_list: List[str]) -> Mapping[str, List[int]]:
    def new_tuple():
        return [0] * WORDLE_LEN
    m_matrix = collections.defaultdict(new_tuple)
    n_matrix = collections.defaultdict(new_tuple)
    for word in word_list:
        letters_in_word = set(word)
        for i, c in enumerate(word):
            m_matrix[c][i] += 1
            for k in letters_in_word:
                if k != c:
                    n_matrix[k][i] += 1
    return m_matrix, n_matrix

class Prior:
    eliminated_letters: Set[str]

    # In the list,
    # - 1 represents that the letter is known to be at this location.
    # - -1 represents that the letter is known _not_ to be at this location.
    # - 0 indicates that the letter may or may not be at this location.
    possible_letter_locations: Dict[str, List[int]]

    def __init__(self):
        self.eliminated_letters = set()

        def new_tuple():
            return [0] * WORDLE_LEN

        self.possible_letter_locations = collections.defaultdict(new_tuple)

    def __str__(self) -> str:
        return f"Prior(eliminated_letters={self.eliminated_letters}, possible_letter_locations={self.possible_letter_locations})"

    __repr__ = __str__


def score_word(word: str, M: Mapping[str, List[int]], N: Mapping[str, List[int]], W: int, prior: Prior) -> float:
    # Award points for:
    #  - Determining whether a letter is in the word
    #  - Determining the placement of a particular letter

    score = 0
    for i, c in enumerate(word):
        if c in prior.eliminated_letters:
            # We gain no new information from this letter.
            continue
        elif c not in prior.possible_letter_locations.keys():
            if c in word[:i]:
                continue
            if W == M[c][i]:
                continue
            # This will tell us whether the letter is in the word or not.
            p1 = M[c][i] / W
            e1 = W - M[c][i]
            p2 = N[c][i] / e1
            e2 = W - N[c][i]
            e3 = M[c][i] + N[c][i]
            e4 = (p2 * e2) + ((1 - p2) * e3)
            score += (p1 * e1) + ((1 - p1) * e4)
        else:
            # This will help clarify the placement of a letter already known to
            # be in the word.
            if prior.possible_letter_locations[c][i] != 0:
                continue
            score += 2 * M[c][i] - 2 * ((M[c][i] ** 2) / W)

    return score


def print_help():
    print("Normal feedback includes the following:")
    print("- X to indicate a missed letter")
    print("- V to indicate the letter is in the word but in the incorrect place")
    print("- O to indicate a correctly placed letter")
    print()
    print("If the word is not in the wordle dictionary, type N/A to generate a new suggestion.")


def is_valid_feedback(cmd: str) -> bool:
    if len(cmd) != WORDLE_LEN:
        return False
    for c in cmd:
        if c not in FEEDBACK_CHARS:
            return False
    return True


class GameState:
    word_list: List[str]
    quiet: bool
    prior: Prior
    m: Mapping[str, List[int]]
    n: Mapping[str, List[int]]
    W: int
    scored_words: List[Tuple[str, int]]
    sorted_words: List[Tuple[str, int]]
    candidate_index: int

    def __init__(self, word_list, quiet):
        self.word_list = word_list
        self.quiet = quiet
        self.prior = Prior()
        self.recalculate_scores()

    def candidate(self):
        return self.sorted_words[0][0]

    def invalidate_candidate(self):
        invalid_index = self.word_list.index(self.candidate())
        self.word_list.pop(invalid_index)
        self.recalculate_scores()

    def print_candidate(self):
        if not self.quiet:
            print(f"{self.sorted_words[0][0]} predicted to eliminate {self.sorted_words[0][1]} words. {len(self.word_list)} remaining.")
        else:
            print(self.sorted_words[0][0])

    def update_from_feedback(self, feedback):
        word = self.candidate()
        for i, (c, feedback_char) in enumerate(zip(word, feedback)):
            if feedback_char == "x":
                self.prior.eliminated_letters |= {c}
            elif feedback_char == "v":
                self.prior.possible_letter_locations[c][i] = -1
            else: # feedback_char == "o"
                self.prior.possible_letter_locations[c][i] = 1
                for other_char in CHARACTERS:
                    if other_char == c:
                        continue
                    if self.prior.possible_letter_locations[other_char][i] == 1:
                        raise AssertionError(f"Conflicting information. Location {i} cannot be both {c} and {other_char}.")
                    self.prior.possible_letter_locations[other_char][i] = -1
        self.filter_word_list()
        self.recalculate_scores()

    def is_valid(self, word) -> bool:
        for c in self.prior.eliminated_letters:
            if c in word:
                return False
        for i, c in enumerate(word):
            if self.prior.possible_letter_locations[c][i] == -1:
                return False
        return True

    def filter_word_list(self):
        new_word_list = []
        for word in self.word_list:
            if self.is_valid(word):
                new_word_list.append(word)
        self.word_list = new_word_list

    def recalculate_scores(self):
        if len(self.word_list) == 0:
            raise AssertionError("No candidate words remaining.")
        self.m, self.n = get_matrices(self.word_list)
        self.scored_words = [(word, score_word(word, self.m, self.n, len(self.word_list), self.prior)) for word in self.word_list]
        self.sorted_words = sorted(self.scored_words,
                        reverse=True,
                        key=lambda x: x[1])

    def print_word_list(self):
        for elem in self.sorted_words:
            print(elem[0])

    def print_success(self):
        if not self.quiet:
            print("🎉🎉 Yay! 🎉🎉")
        else:
            print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve Wordle.")
    parser.add_argument("-q", "--quiet",
                        action="store_true",
                        help="If set, outputs much less. Suitable for machine parsing.")
    args = parser.parse_args()
    prompt = "> "
    if args.quiet:
        prompt = ""

    word_list = initial_word_list()
    game_state = GameState(word_list, args.quiet)
    game_state.print_candidate()

    while True:
        cmd = input(prompt).strip().lower()
        if cmd == "help":
            print_help()
        elif cmd in ("quit", "exit"):
            break
        elif cmd == "n/a":
            game_state.invalidate_candidate()
            game_state.print_candidate()
        elif cmd == "list":
            game_state.print_word_list()
        elif cmd == "debug":
            print(game_state.prior)
        elif cmd == "ooooo":
            game_state.print_success()
        elif is_valid_feedback(cmd):
            game_state.update_from_feedback(cmd)
            game_state.print_candidate()
        else:
            print_help()
