#!/usr/bin/env python3

"""New York Times Wordle Puzzle Solver v1.0.

USAGE

    wordle_solver.py webdemo
      demonstrates solving a Wordle puzzle on the NYT website;
      requires selenium and webdriver-manager to be installed.

    wordle_solver.py demo
      demonstrates solving a Wordle puzzle locally.

    wordle_solver.py solve
      helps you solve a Wordle puzzle (https://www.nytimes.com/games/wordle/index.html);
      here's how it works:
      
      1. The tool tells you what you should guess next.
      2. You type the guess into the Wordle game.
      3. The game gives you hints based on the guess.
      4. You tell the tool what the hints are; for example, 'OMXXX' means that
         the first letter of the guess is in the answer but at a wrong spot,
         the second letter of the guess is in the answer and at the right spot,
         and the remaining letters of the guess are not in the answer.
      5. Repeat the above steps.

      This tool's strategy conforms to the game's hard mode. I.e. it only makes
      guesses that conform to all revealed hints.

    wordle_solver.py test
      tests the algorithm with all possible answers.

    wordle_solver.py triples
      updates src/best-triples.txt with the best triple words.
"""

from collections import defaultdict
from datetime import datetime
from typing import Callable, Dict, List, Tuple

import os
import random
import sys
import time

WEB_AUTOMATION = True
try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.common.by import By
except ModuleNotFoundError:
    print(
        "To automate interaction with the game site, run 'pip install selenium' "
        "to install the selenium python binding."
    )
    WEB_AUTOMATION = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError:
    print(
        "To automate interaction with the game site, run 'pip install webdriver-manager' "
        "to install the webdriver-manager python library."
    )
    WEB_AUTOMATION = False


def GetWordList(rel_path: str) -> List[str]:
    py_file_dir = os.path.dirname(__file__)
    wordle_list_file = os.path.join(py_file_dir, rel_path)
    words = []
    with open(wordle_list_file, "r") as f:
        for line in f.readlines():
            word = line.strip().upper()
            if len(word) == 5:
                words.append(word)
    return words


VALID_ANSWERS = GetWordList("valid-answers.txt")
VALID_ANSWER_SET = set(VALID_ANSWERS)
VALID_NON_ANSWER_GUESSES = GetWordList("valid-guesses.txt")
ALL_WORDS = VALID_ANSWERS + VALID_NON_ANSWER_GUESSES


def GetLetterFrequencies(words: List[str]) -> Dict[str, int]:
    letter_freq = defaultdict(int)
    for word in words:
        # Only consider valid answer words when calcultating letter frequencies.
        if word not in VALID_ANSWER_SET:
            continue

        for letter in word:
            letter_freq[letter] += 1
    return letter_freq


def GetWordWithHighestLetterFrequencies(
    words_for_freq: List[str], candidates: List[str]
) -> str:
    # Precondition.
    assert words_for_freq
    assert candidates

    letter_freq = GetLetterFrequencies(words_for_freq)
    best_word = None
    max_freq = 0
    for word in candidates:
        freq = sum(letter_freq[ch] for ch in set(word))
        if freq > max_freq:
            max_freq = freq
            best_word = word
    assert best_word is not None
    return best_word


def GetWordLetterFrequency(word: str, letter_freq: Dict[str, int]) -> int:
    return sum(letter_freq[letter] for letter in set(word))


# This returns 300 best pairs.  TODO: find which of the 300 is the best.
def GetWordPairsWithHighestLetterFrequencies(words: List[str]) -> List[Tuple[str, str]]:
    letter_freq = GetLetterFrequencies(words)
    candidates = words
    candidate_freqs = [
        (word, GetWordLetterFrequency(word, letter_freq)) for word in candidates
    ]
    candidate_to_freq = {pair[0]: pair[1] for pair in candidate_freqs}
    sorted_candidate_freqs = sorted(
        candidate_freqs, key=lambda pair: pair[1], reverse=True
    )
    sorted_candidates = [pair[0] for pair in sorted_candidate_freqs]
    best_pairs = []
    max_freq = 0
    num_words = len(sorted_candidates)
    for i, word1 in enumerate(sorted_candidates):
        word1_freq = candidate_to_freq[word1]
        for j in range(i + 1, num_words):
            word2 = sorted_candidates[j]
            word2_freq = candidate_to_freq[word2]
            # Optimization: the letter frequency of (word1, word2) is at most
            # the letter frequency of word1 + the letter frequency of word2
            # (it can be smaller as word1 and word2 may contain overlapping
            # letters).  Therefore there's no need to try the remaining possible
            # word2 values if they cannot possibly beat max_freq.
            if word1_freq + word2_freq < max_freq:
                break
            freq = GetWordLetterFrequency(word1 + word2, letter_freq)
            if freq > max_freq:
                max_freq = freq
                best_pairs = [(word1, word2)]
            elif freq == max_freq:
                best_pairs.append((word1, word2))
    return best_pairs


def NormalizeWordAsLetterSet(word: str) -> str:
    # hello => ehlo
    # basic => abcis
    return "".join(sorted(set(word)))


def GetWordTriplesWithHighestLetterFrequencies(
    words: List[str],
) -> List[Tuple[str, str, str]]:
    letter_freq = GetLetterFrequencies(words)
    candidate_words = words

    # For the purpose of letter frequency coverage, the order of the letters
    # in a word and duplicated letters don't matter.  Therefore we can treat
    # a word as a set of letters.  This allows us to merge words that consist
    # of the same letters (i.e. anagrams).  For example, we don't have to
    # consider SALES and LESSA as different words as they contain the same
    # set of letters.  With this optimization, we only need to consider 7622
    # candidates instead of 12947.  This greatly speeds up this function,
    # which has O(N^3) time complexity.
    candidate_to_word = {
        NormalizeWordAsLetterSet(word): word for word in candidate_words
    }
    candidates = candidate_to_word.keys()
    candidate_freqs = [
        (candidate, GetWordLetterFrequency(candidate, letter_freq))
        for candidate in candidates
    ]
    candidate_to_freq = {pair[0]: pair[1] for pair in candidate_freqs}
    sorted_candidate_freqs = sorted(
        candidate_freqs, key=lambda pair: pair[1], reverse=True
    )
    sorted_candidates = [pair[0] for pair in sorted_candidate_freqs]
    best_triples = []
    max_freq = 0
    num_candidates = len(sorted_candidates)
    print(f"Processing {num_candidates} candidates.")
    for i, candidate1 in enumerate(sorted_candidates):
        word1 = candidate_to_word[candidate1]
        print(f"{i} - {word1}")
        candidate1_freq = candidate_to_freq[candidate1]
        for j in range(i + 1, num_candidates):
            candidate2 = sorted_candidates[j]
            word2 = candidate_to_word[candidate2]
            candidate2_freq = candidate_to_freq[candidate2]
            if candidate1_freq + 2 * candidate2_freq < max_freq:
                break
            candidate1_2_freq = GetWordLetterFrequency(
                candidate1 + candidate2, letter_freq
            )
            for k in range(j + 1, num_candidates):
                candidate3 = sorted_candidates[k]
                candidate3_freq = candidate_to_freq[candidate3]
                if candidate1_2_freq + candidate3_freq < max_freq:
                    break
                freq = GetWordLetterFrequency(
                    candidate1 + candidate2 + candidate3, letter_freq
                )
                if freq >= max_freq:
                    triple = (word1, word2, candidate_to_word[candidate3])
                    if freq > max_freq:
                        max_freq = freq
                        best_triples = [triple]
                    else:  # freq == max_freq
                        best_triples.append(triple)
    return best_triples


def GetHints(guess: str, answer: str) -> str:
    hints = ""
    for i, letter in enumerate(guess):
        if letter == answer[i]:
            hint = "M"  # The letter and its position are correct.
        elif letter in answer:
            hint = "O"  # The letter is in the answer, but in a different position.
        else:
            hint = "X"  # The letter is not in the answer.
        hints += hint
    return hints


def MatchesHints(word: str, guess: str, hints: str) -> bool:
    for i, hint in enumerate(hints):
        if hint == "M":
            if word[i] != guess[i]:
                return False
        elif hint == "O":
            if word[i] == guess[i]:
                return False
            elif guess[i] not in word:
                return False
        else:
            if guess[i] in word:
                return False
    return True


def FilterByHints(words: List[str], guess: str, hints: str) -> List[str]:
    return [word for word in words if MatchesHints(word, guess, hints)]


def Colored(r: int, g: int, b: int, text: str) -> str:
    return f"\033[38;2;{r};{g};{b}m{text}\033[38;2;255;255;255m"


def FormatHints(guess: str, hints: str) -> str:
    formatted = ""
    for i, letter in enumerate(guess):
        hint = hints[i]
        if hint == "X":
            formatted += Colored(127, 127, 127, letter)
        elif hint == "O":
            formatted += Colored(255, 255, 0, letter)
        else:
            formatted += Colored(0, 255, 0, letter)
    return formatted


class WordleSolverBase:
    """Base class for wordle solvers."""

    def __init__(self):
        self.guess_hints = []  # Hints received so far.
        self.candidates = ALL_WORDS[:]  # Valid guesses that satisfy all hints so far.

    def SuggestGuess(self) -> str:
        """Subclasses should implement this to return a suggested guess or None."""
        raise Exception("Not implemented.")

    def MakeGuess(self, guess: str, hints: str) -> None:
        assert guess in ALL_WORDS, f"{guess} is an invalid word."
        self.guess_hints.append((guess, hints))
        self.candidates = FilterByHints(self.candidates, guess, hints)

    def RestrictCandidatesToValidAnswers(self) -> None:
        self.candidates = [word for word in self.candidates if word in VALID_ANSWER_SET]


class HardModeEagerWordleSolver(WordleSolverBase):
    """A hard-mode solver that always tries the most likely word.

    Tested 12947 words.
    Failed: 1624 words 12.54%.
    1 guesses: 1 words 0.01%.
    2 guesses: 163 words 1.26%.
    3 guesses: 1968 words 15.20%.
    4 guesses: 4434 words 34.25%.
    5 guesses: 3208 words 24.78%.
    6 guesses: 1549 words 11.96%.

    Tested 2309 possible answers.
    Failed: 14 words 0.61%.
    1 guesses: 1 words 0.04%.
    2 guesses: 133 words 5.76%.
    3 guesses: 888 words 38.46%.
    4 guesses: 944 words 40.88%.
    5 guesses: 269 words 11.65%.
    6 guesses: 60 words 2.60%.
    """

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses == 0:
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class IgnoreEarliestHintsWordleSolver(WordleSolverBase):
    """A solver that always chooses from the entire word list in its first 2 tries.

    Tested 12947 words.
    Failed: 1642 words 12.68%.
    1 guesses: 1 words 0.01%.
    2 guesses: 64 words 0.49%.
    3 guesses: 1900 words 14.68%.
    4 guesses: 4427 words 34.19%.
    5 guesses: 3321 words 25.65%.
    6 guesses: 1592 words 12.30%.

    Tested 2309 possible answers.
    Failed: 30 words 1.30%.
    1 guesses: 1 words 0.04%.
    2 guesses: 35 words 1.52%.
    3 guesses: 815 words 35.30%.
    4 guesses: 1017 words 44.05%.
    5 guesses: 327 words 14.16%.
    6 guesses: 84 words 3.64%.
    """

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses == 2:
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(
            self.candidates, ALL_WORDS if num_guesses < 2 else self.candidates
        )


class AudioLeftyWordleSolver(WordleSolverBase):
    """A solver that tries audio and lefty first.

    Tested 12947 words.
    Failed: 1214 words 9.38%.
    1 guesses: 1 words 0.01%.
    2 guesses: 1 words 0.01%.
    3 guesses: 1426 words 11.01%.
    4 guesses: 4707 words 36.36%.
    5 guesses: 3988 words 30.80%.
    6 guesses: 1610 words 12.44%.

    Tested 2309 possible answers.
    Failed: 33 words 1.43%.
    1 guesses: 1 words 0.04%.
    2 guesses: 1 words 0.04%.
    3 guesses: 370 words 16.02%.
    4 guesses: 1284 words 55.61%.
    5 guesses: 516 words 22.35%.
    6 guesses: 104 words 4.50%.
    """

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses == 0:
            return "AUDIO"
        if num_guesses == 1:
            return "LEFTY"
        if num_guesses == 3:
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class AudioWordleSolver(WordleSolverBase):
    """A solver that tries audio first.

    Tested 12947 words.
    Failed: 1559 words 12.04%.
    1 guesses: 1 words 0.01%.
    2 guesses: 140 words 1.08%.
    3 guesses: 1828 words 14.12%.
    4 guesses: 4464 words 34.48%.
    5 guesses: 3343 words 25.82%.
    6 guesses: 1612 words 12.45%.

    Tested 2309 possible answers.
    Failed: 39 words 1.69%.
    1 guesses: 1 words 0.04%.
    2 guesses: 29 words 1.26%.
    3 guesses: 770 words 33.35%.
    4 guesses: 1038 words 44.95%.
    5 guesses: 346 words 14.98%.
    6 guesses: 86 words 3.72%.
    """

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses == 0:
            return "AUDIO"
        if num_guesses == 2:  # 2,3,5 => 1.69%
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class TwoCoverWordleSolver(WordleSolverBase):
    """A solver that tries to cover the highest-frequency letters in the first 2 guesses.

    Tested 12947 words.
    Failed: 1150 words 8.88%.
    1 guesses: 1 words 0.01%.
    2 guesses: 1 words 0.01%.
    3 guesses: 2170 words 16.76%.
    4 guesses: 5100 words 39.39%.
    5 guesses: 3225 words 24.91%.
    6 guesses: 1300 words 10.04%.

    Tested 2309 possible answers.
    Failed: 23 words 1.00%.
    3 guesses: 927 words 40.15%.
    4 guesses: 998 words 43.22%.
    5 guesses: 296 words 12.82%.
    6 guesses: 65 words 2.82%.
    """

    def __init__(self):
        super().__init__()
        # Set best_pair to the result of GetWordPairsWithHighestLetterFrequencies(ALL_WORDS).
        # We hard code the words here as it's slow to call this function.
        # pairs = GetWordPairsWithHighestLetterFrequencies(ALL_WORDS)
        # print(f'Found {len(pairs)} best pairs: {pairs}')  # 300 pairs.
        self.best_pair = ("STARN", "LOUIE")

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses < 2:
            return self.best_pair[num_guesses]
        if num_guesses == 2:
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class ThreeCoverWordleSolver(WordleSolverBase):
    """A solver that tries to cover the highest-frequency letters in the first 3 guesses.

    For 'AEROS', 'CLINT', 'DUMPY':
      Failed: 636 words 4.91%.

    For 'MUTES', 'PLAID', 'CORNY':
      Failed: 643 words 4.97%.

    For 'EPICS', 'NOMAD', 'TRULY':
      Failed: 652 words 5.04%.

    For 'LYRIC', 'UPSET', 'NOMAD':
      Tested 12947 words.
      Failed: 617 words 4.77%.
      1 guesses: 1 words 0.01%.
      2 guesses: 1 words 0.01%.
      3 guesses: 1 words 0.01%.
      4 guesses: 6377 words 49.25%.
      5 guesses: 4710 words 36.38%.
      6 guesses: 1240 words 9.58%.

      Tested 2309 possible answers.
      Failed: 10 words 0.43%.
      1 guesses: 1 words 0.04%.
      2 guesses: 1 words 0.04%.
      3 guesses: 1 words 0.04%.
      4 guesses: 1478 words 64.01%.
      5 guesses: 745 words 32.27%.
      6 guesses: 73 words 3.16%.
    """

    def __init__(self):
        super().__init__()
        # Set best_triple to the result of GetWordTriplesWithHighestLetterFrequencies(ALL_WORDS).
        self.best_triple = ("LYRIC", "UPSET", "NOMAD")

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses < 3:
            return self.best_triple[num_guesses]
        if num_guesses == 4:
            # After 4 guesses, only try words that are valid answer words.
            self.RestrictCandidatesToValidAnswers()
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class ExperiencedThreeCoverWordleSolver(WordleSolverBase):
    """A solver that tries to cover the highest-frequency letters in the first 3 guesses and uses experience to improve the odds.

    Tested 2309 possible answers.
    1 guesses: 1 words 0.04%.
    2 guesses: 45 words 1.95%.
    3 guesses: 524 words 22.69%.
    4 guesses: 1223 words 52.97%.
    5 guesses: 452 words 19.58%.
    6 guesses: 64 words 2.77%.
    Average # of guesses: 3.984.
    """

    def __init__(self):
        super().__init__()
        # Set best_triple to the result of GetWordTriplesWithHighestLetterFrequencies(ALL_WORDS).
        self.best_triple = ("LYRIC", "UPSET", "NOMAD")

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses < 3:
            # Switch from exploration mode to solution mode early if there aren't
            # many remaining words.
            threshold = 3 ** (3 - num_guesses) * 4
            if len(self.candidates) <= threshold:
                self.RestrictCandidatesToValidAnswers()
                return GetWordWithHighestLetterFrequencies(
                    self.candidates, self.candidates
                )

            return self.best_triple[num_guesses]
        if num_guesses == 3:
            if self.guess_hints == [
                ("LYRIC", "XXXXX"),
                ("UPSET", "OXXXM"),
                ("NOMAD", "OXXOX"),
            ]:
                return "VUGHS"
            if self.guess_hints == [
                ("LYRIC", "XXXXO"),
                ("UPSET", "XXXXO"),
                ("NOMAD", "XXXOX"),
            ]:
                return "CROWS"
            if self.guess_hints == [
                ("LYRIC", "XXXXX"),
                ("UPSET", "OXXXX"),
                ("NOMAD", "OMXXM"),
            ]:
                return "FROWN"
            if self.guess_hints == [
                ("LYRIC", "OXOOX"),
                ("UPSET", "XXXXX"),
                ("WHIRL", "XXMOM"),
            ]:
                return "GREEK"
        if num_guesses == 4:
            # After 4 guesses, only try words that are valid answer words.
            self.RestrictCandidatesToValidAnswers()
            if self.guess_hints == [
                ("LYRIC", "XXOXX"),
                ("UPSET", "XXXMX"),
                ("NOMAD", "XMXXX"),
                ("WOKER", "XMXMM"),
            ]:
                return "RAVES"
            if self.guess_hints == [
                ("LYRIC", "XXXXX"),
                ("UPSET", "XXMOO"),
                ("NOMAD", "XXXOX"),
                ("WASTE", "XMMMM"),
            ]:
                return "TOOTH"
            if self.guess_hints == [
                ("LYRIC", "XXXXX"),
                ("UPSET", "XXOOO"),
                ("NOMAD", "XXXOX"),
                ("STAKE", "MMMXM"),
            ]:
                return "GOATS"
            if self.guess_hints == [
                ("LYRIC", "OXOOX"),
                ("UPSET", "XXXXX"),
                ("NOMAD", "XXXXX"),
                ("WHIRL", "XXMOM"),
            ]:
                return "FROGS"
            if self.guess_hints == [
                ("LYRIC", "OOXXX"),
                ("UPSET", "XXXXX"),
                ("NOMAD", "XMXXX"),
                ("JOWLY", "XMXMM"),
            ]:
                return "FROGS"
            if self.guess_hints == [
                ("LYRIC", "OOXOX"),
                ("UPSET", "XXXXX"),
                ("NOMAD", "XXXXX"),
                ("BIGLY", "XMXMM"),
            ]:
                return "FROWN"
            if self.guess_hints == [
                ("LYRIC", "XXOXX"),
                ("UPSET", "XXXMX"),
                ("NOMAD", "XMXXX"),
                ("VOWER", "XMXMM"),
            ]:
                return "BOOKS"
            if self.guess_hints == [
                ("LYRIC", "OOXOX"),
                ("UPSET", "XXXXX"),
                ("NOMAD", "XXXXX"),
                ("FILLY", "XMMMM"),
            ]:
                return "HOBBY"
            if self.guess_hints == [
                ("LYRIC", "OXXXX"),
                ("UPSET", "OXOXX"),
                ("NOMAD", "XXXXX"),
                ("HULKS", "OOOXO"),
            ]:
                return "BARFS"
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


class NewThreeCoverWordleSolver(WordleSolverBase):
    """A solver that tries to cover the highest-frequency letters in the first 3 guesses and uses experience to improve the odds.
    It differs from ExperiencedThreeCoverWordleSolver in that it picks a different
    starting triple, which doesn't consider non-answer words when computing the letter frequencies.

    Tested 2309 possible answers.
    2 guesses: 66 words 2.86%.
    3 guesses: 682 words 29.54%.
    4 guesses: 1157 words 50.11%.
    5 guesses: 350 words 15.16%.
    6 guesses: 54 words 2.34%.
    Average # of guesses: 3.846.
    """

    def __init__(self):
        super().__init__()
        # Set best_triple to the result of GetWordTriplesWithHighestLetterFrequencies(ALL_WORDS).
        self.best_triple = ("ROATE", "PULIS", "CHYND")

    def SuggestGuess(self) -> str:
        num_guesses = len(self.guess_hints)
        if num_guesses < 3:
            if self.guess_hints == [("ROATE", "XXOMM"), ("SAUTE", "OMXMM")]:
                return "CHIPS"
            # Switch from exploration mode to solution mode early if there aren't
            # many remaining words.
            threshold = 3 ** (3 - num_guesses) * 4
            if len(self.candidates) <= threshold:
                self.RestrictCandidatesToValidAnswers()
                return GetWordWithHighestLetterFrequencies(
                    self.candidates, self.candidates
                )

            return self.best_triple[num_guesses]
        if num_guesses == 3:
            if self.guess_hints == [
                ("ROATE", "XMXXX"),
                ("PULIS", "XOXXX"),
                ("CHYND", "XXXMM"),
            ]:
                return "BOWER"
            if self.guess_hints == [
                ("ROATE", "OXOXO"),
                ("PULIS", "XXXXX"),
                ("CHYND", "XXXXX"),
            ]:
                return "WAGER"
            if self.guess_hints == [
                ("ROATE", "OXOOO"),
                ("PULIS", "XXXXX"),
                ("CHYND", "XXXXX"),
            ]:
                return "TAMER"
            if self.guess_hints == [
                ("ROATE", "XXOOX"),
                ("PULIS", "XOXXX"),
                ("CHYND", "XXXMX"),
            ]:
                return "TANGO"
            if self.guess_hints == [
                ("ROATE", "XXOOX"),
                ("PULIS", "XXXXX"),
                ("CHYND", "OOXXX"),
            ]:
                return "BROWN"
        if num_guesses == 4:
            # After 4 guesses, only try words that are valid answer words.
            self.RestrictCandidatesToValidAnswers()
            if self.guess_hints == [
                ("ROATE", "XXXOX"),
                ("PULIS", "XXXOX"),
                ("CHYND", "XOXXX"),
                ("MIGHT", "XMMMM"),
            ]:
                return "FROWN"
            if self.guess_hints == [
                ("ROATE", "OXXXO"),
                ("PULIS", "XXXXX"),
                ("CHYND", "XXOXX"),
                ("JERKY", "XMMXM"),
            ]:
                return "BLOOM"
        return GetWordWithHighestLetterFrequencies(self.candidates, self.candidates)


def TrySolve(solver: WordleSolverBase, answer: str, show_process: bool = True) -> int:
    """Returns the number of attempts (0 means failed)."""

    for attempt in range(6):
        guess = solver.SuggestGuess()
        if not guess:
            if show_process:
                print("Hmm, I ran out of ideas.")
            return 0
        if show_process:
            print(f"Guess #{attempt +1}: {guess}")
        hints = GetHints(guess, answer)
        if hints == "MMMMM":
            if show_process:
                print(f"Success!  The answer is {FormatHints(guess, hints)}.")
            return attempt + 1
        if show_process:
            print(f"Hints: {FormatHints(guess, hints)}")
        solver.MakeGuess(guess, hints)
    if show_process:
        print("Oops, I ran out of attempts.")
    return 0


def GetKeyIndexInGameKeyboard(key: str) -> int:
    """Returns the index of the given key in the game's keyboard."""
    keyboard = "qwertyuiopasdfghjkl\nzxcvbnm<"
    return keyboard.find(key.lower())


def GetGuessFromWeb(remaining_tiles) -> str:
    """Returns the guess shown in the given tiles on the game's website.

    Args:
        tiles: a list of letter tiles on the website; we only care about
               the first 5 of them.
    """

    guess = ""
    for tile in remaining_tiles[:5]:
        guess += tile.text
    return guess


def GetHintsFromWeb(tiles) -> str:
    """Returns the hints shown in the given tiles on the game's website.

    Args:
        tiles: a list of letter tiles on the website; we only care about
               the first 5 of them.
    """

    hints = ""
    for tile in tiles[:5]:
        state = tile.get_attribute("data-state")
        if state == "correct":
            hints += "M"
        elif state == "present":
            hints += "O"
        elif state == "absent":
            hints += "X"
    return hints


def TrySolveWeb(driver: webdriver.Chrome, solver: WordleSolverBase) -> int:
    """Solves the game on the NYT website.

    Returns:
        the number of attempts (0 means failed).
    """

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print(f"Current Time: {current_time}")

    for attempt in range(3):
        driver.get("https://www.nytimes.com/games/wordle/index.html")
        print("Starting the game in 3 seconds...")
        time.sleep(3)

        try:
            close_icon = driver.find_element(
                by=By.CLASS_NAME, value="Modal-module_closeIcon__b4z74"
            )
            close_icon.click()
            break
        except NoSuchElementException:
            print("Found no close icon!")
            time.sleep(5)

    time.sleep(2)  # Wait for the initial pop-up to be dismissed.

    # Find the elements on the game page for interaction.
    keyboard = driver.find_elements(By.CLASS_NAME, "Key-module_key__Rv-Vp")
    assert len(keyboard) == 28, f"Unexpected number of keys: {len(keyboard)}"
    tiles = driver.find_elements(By.CLASS_NAME, "Tile-module_tile__3ayIZ")
    assert len(tiles) == 5 * 6, f"Unexpected number of tiles: {len(tiles)}"

    for attempt in range(6):
        remaining_tiles = tiles[5 * attempt :]
        num_candidates = len(solver.candidates)
        print(f"{num_candidates} candidates remaining.")
        if num_candidates <= 10:
            print(" ".join(sorted(solver.candidates)))

        guess = GetGuessFromWeb(remaining_tiles)
        if guess:
            print(f"Using pre-existing guess from the game: {guess}.")
        else:  # No pre-existing guess.
            # Let the solver make a guess.
            guess = solver.SuggestGuess()
            print(f"Guess #{attempt + 1}: {guess}")
            if not guess:
                return 0
            for char in guess + "\n":
                keyboard[GetKeyIndexInGameKeyboard(char)].click()
                time.sleep(0.2)
            time.sleep(2)
        hints = GetHintsFromWeb(remaining_tiles)
        print(f"Hints: {hints}")
        if len(hints) != 5:
            print("Invalid hints.  Will retry the game later.")
            return 0
        if hints == "MMMMM":
            print(f"You win with {attempt + 1} guesses!")
            return attempt + 1
        solver.MakeGuess(guess, hints)
    return 0


def WebDemo(solver_factory: Callable[[], WordleSolverBase]) -> None:
    """Demostrates solving the game on the NYT website."""

    print("Downloading web driver...")
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=chrome_options
    )
    while True:
        TrySolveWeb(driver, solver_factory())
        print("Restarting the game in 1 hour...")
        time.sleep(60 * 60)


def Demo(solver_factory: Callable[[], WordleSolverBase]) -> None:
    """Demostrates solving the game locally."""

    random.seed()
    answer = random.choice(VALID_ANSWERS)
    TrySolve(solver_factory(), answer)


def TestSolver(solver_factory: Callable[[], WordleSolverBase]) -> None:
    total_num_answers = len(VALID_ANSWERS)
    failed = []
    guess_freq = defaultdict(int)  # Maps # of guesses to frequency.
    for i, answer in enumerate(VALID_ANSWERS):
        solver = solver_factory()
        num_guesses = TrySolve(solver, answer, show_process=False)
        guess_freq[num_guesses] += 1
        if not num_guesses:
            print(
                f"Failed to solve for answer {answer} (word {i} out of {total_num_answers})."
            )
            print(f"Trial history: {solver.guess_hints}")
            failed.append(answer)

    # Print statistics.
    print(f"Tested {total_num_answers} possible answers.")
    total_guesses = 0
    for num_guesses in sorted(guess_freq.keys()):
        if num_guesses:
            prefix = f"{num_guesses} guesses"
        else:
            prefix = "Failed"
        num_words = guess_freq[num_guesses]
        total_guesses += num_words * (num_guesses if num_guesses else 7)
        print(f"{prefix}: {num_words} words {num_words*100.0/total_num_answers:.2f}%.")
    print(f"Average # of guesses: {total_guesses / total_num_answers:.3f}.")


def IsValidGuess(guess: str) -> bool:
    return guess in ALL_WORDS


def IsValidHints(hints: str) -> bool:
    if len(hints) != 5:
        return False
    for hint in hints:
        if hint not in "MOX":
            return False
    return True


def Solve(solver_factory: Callable[[], WordleSolverBase]) -> None:
    solver = solver_factory()
    for attempt in range(6):
        suggested_guess = solver.SuggestGuess()
        if not suggested_guess:
            print("Hmm, I ran out of ideas.")

        print(f"{len(solver.candidates)} words satisfy all hints so far.")
        while True:
            guess = input(
                f"What is your guess #{attempt + 1} (I suggest {suggested_guess})? "
                "Press <enter> to see all words that satisfy the existing hints. "
            ).upper()
            if not guess:
                print("These words satisfy all hints so far:")
                print(", ".join(sorted(solver.candidates)))
                continue
            if IsValidGuess(guess):
                break
            print("Invalid guess.  Please type again.")
        while True:
            hints = input(
                "What are the hints you got (5-letter string, where M = match, "
                "O = wrong order, X: not match)? "
            ).upper()
            if IsValidHints(hints):
                break
            print("Invalid hints.  Please type again.")
        if hints == "MMMMM":
            print(f"Success!  The answer is {FormatHints(guess, hints)}.")
            break
        print(f"Hint: {FormatHints(guess, hints)}")
        solver.MakeGuess(guess, hints)


def PrintLetterFrequencies() -> None:
    freqs = list(GetLetterFrequencies(ALL_WORDS).items())
    sorted_freqs = sorted(freqs, key=lambda pair: pair[1], reverse=True)
    for letter, freq in sorted_freqs:
        print(f"{letter}: {freq}")


def PrintWordsWithHighestLetterFrequencies() -> None:
    letter_freqs = GetLetterFrequencies(ALL_WORDS)
    word_freq_pairs = []
    for word in ALL_WORDS:
        freq = sum(letter_freqs[ch] for ch in set(word))
        word_freq_pairs.append((word, freq))
    sorted_word_freq_pairs = sorted(
        word_freq_pairs, key=lambda pair: pair[1], reverse=True
    )
    for word, freq in sorted_word_freq_pairs[:10]:
        print(f"{word}: {freq}")
    for word, freq in sorted_word_freq_pairs[-10:]:
        print(f"{word}: {freq}")


def FindBestTriples() -> None:
    triples = GetWordTriplesWithHighestLetterFrequencies(ALL_WORDS)
    py_file_dir = os.path.dirname(__file__)
    triple_list_file = os.path.join(py_file_dir, "best-triples.txt")
    print(f"Found {len(triples)} best triples.")
    with open(triple_list_file, "w") as f:
        for word1, word2, word3 in triples:
            f.write(f"{word1} {word2} {word3}\n")


def main() -> None:
    print("Welcome to Zhanyong Wan's Wordle Solver!\n")
    args = sys.argv[1:]
    # Valid choices:
    #   AudioLeftyWordleSolver,
    #   AudioWordleSolver,
    #   HardModeEagerWordleSolver,
    #   IgnoreEarliestHintsWordleSolver,
    #   ThreeCoverWordleSolver, (second best)
    #   TwoCoverWordleSolver,
    #   ExperiencedThreeCoverWordleSolver (perfect)
    #   NewThreeCoverWordleSolver (perfect, best)
    solver_factory = NewThreeCoverWordleSolver
    if "demo" in args:
        Demo(solver_factory)
    elif "webdemo" in args:
        if WEB_AUTOMATION:
            WebDemo(solver_factory)
        else:
            print("Web automation is not available. Doing a local demo instead.")
            Demo(solver_factory)
    elif "solve" in args:
        Solve(solver_factory)
    elif "test" in args:
        TestSolver(solver_factory)
    elif "triples" in args:
        FindBestTriples()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
