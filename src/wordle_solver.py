#!/usr/bin/env python3

"""New York Times Wordle Puzzle Solver.

USAGE

    wordle_solver.py demo
      demonstrates solving a Wordle puzzle.

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
"""

from collections import defaultdict

import os
import random
import sys

def GetWordList():
  py_file_dir = os.path.dirname(__file__)
  wordle_list_file = os.path.join(py_file_dir, '../wordle-list/words')
  words = []
  with open(wordle_list_file, 'r') as f:
    for line in f.readlines():
      word = line.strip().upper()
      if len(word) == 5:
        words.append(word)
  return words

ALL_WORDS = GetWordList()

def GetLetterFrequencies(words):
  letter_freq = defaultdict(int)
  for word in words:
    for letter in word:
      letter_freq[letter] += 1
  return letter_freq

def GetWordWithHighestLetterFrequencies(words, try_all_words=False):
  letter_freq = GetLetterFrequencies(words)
  candidates = ALL_WORDS if try_all_words else words
  best_word = None
  max_freq = 0
  for word in candidates:
    freq = sum(letter_freq[ch] for ch in set(word))
    if freq > max_freq:
      max_freq = freq
      best_word = word
  return best_word

def GetTwoWordsWithHighestLetterFrequencies(words, try_all_words=False):
  letter_freq = GetLetterFrequencies(words)
  candidates = ALL_WORDS if try_all_words else words
  best_pair = None
  max_freq = 0
  for i, word1 in enumerate(candidates):
    for word2 in candidates[i + 1:]:
      freq = sum(letter_freq[ch] for ch in set(word1 + word2))
      if freq > max_freq:
        max_freq = freq
        best_pair = (word1, word2)
  return best_pair

def GetHints(guess, answer):
  hints = ''
  for i, letter in enumerate(guess):
    if letter == answer[i]:
      hint = 'M'  # The letter and its position are correct.
    elif letter in answer:
      hint = 'O'  # The letter is in the answer, but in a different position.
    else:
      hint = 'X'  # The letter is not in the answer.
    hints += hint
  return hints

def MatchesHints(word, guess, hints):
  for i, hint in enumerate(hints):
    if hint == 'M':
      if word[i] != guess[i]:
        return False
    elif hint == 'O':
      if word[i] == guess[i]:
        return False
      elif guess[i] not in word:
        return False
    else:
      if guess[i] in word:
        return False
  return True

def FilterByHints(words, guess, hints):
  return [word for word in words if MatchesHints(word, guess, hints)]

def Colored(r, g, b, text):
  return f'\033[38;2;{r};{g};{b}m{text}\033[38;2;255;255;255m'

def FormatHints(guess, hints):
  formatted = ''
  for i, letter in enumerate(guess):
    hint = hints[i]
    if hint == 'X':
      formatted += Colored(127, 127, 127, letter)
    elif hint == 'O':
      formatted += Colored(255, 255, 0, letter)
    else:
      formatted += Colored(0, 255, 0, letter)
  return formatted

class WordleSolverBase:
  """Base class for wordle solvers."""

  def __init__(self):
    self.guess_hints = []
    self.candidates = ALL_WORDS[:]

  def SuggestGuess(self):
    """Subclasses should implement this to return a suggested guess or None."""
    raise Exception('Not implemented.')

  def MakeGuess(self, guess, hints):
    self.guess_hints.append((guess, hints))
    self.candidates = FilterByHints(self.candidates, guess, hints)

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
  """

  def SuggestGuess(self):
    return GetWordWithHighestLetterFrequencies(self.candidates)

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
  """

  def SuggestGuess(self):
    num_guesses = len(self.guess_hints)
    return GetWordWithHighestLetterFrequencies(self.candidates, try_all_words=num_guesses < 2)

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
  """

  def SuggestGuess(self):
    num_guesses = len(self.guess_hints)
    if num_guesses == 0:
      return 'AUDIO'
    if num_guesses == 1:
      return 'LEFTY'
    return GetWordWithHighestLetterFrequencies(self.candidates)

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
  """

  def SuggestGuess(self):
    num_guesses = len(self.guess_hints)
    if num_guesses == 0:
      return 'AUDIO'
    return GetWordWithHighestLetterFrequencies(self.candidates)

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
  """

  def __init__(self):
    super().__init__()
    # Set best_pair to the result of GetTwoWordsWithHighestLetterFrequencies(ALL_WORDS).
    # We hard code the words here as it's slow to call the GetTwoWords*() function.
    self.best_pair = ('STARN', 'LOUIE')

  def SuggestGuess(self):
    num_guesses = len(self.guess_hints)
    if num_guesses < 2:
      return self.best_pair[num_guesses]
    return GetWordWithHighestLetterFrequencies(self.candidates)

def TrySolve(solver, answer, show_process=True):
  """Returns the number of attempts (0 means failed)."""

  for attempt in range(6):
    guess = solver.SuggestGuess()
    if not guess:
      if show_process:
        print('Hmm, I ran out of ideas.')
      return 0
    if show_process:
      print(f'Guess #{attempt +1}: {guess}')
    hints = GetHints(guess, answer)
    if hints == 'MMMMM':
      if show_process:
        print(f'Success!  The answer is {FormatHints(guess, hints)}.')
      return attempt + 1
    if show_process:
      print(f'Hints: {FormatHints(guess, hints)}')
    solver.MakeGuess(guess, hints)
  if show_process:
    print('Oops, I ran out of attempts.')
  return 0

def Demo(solver_factory):
  random.seed()
  answer = random.choice(ALL_WORDS)
  TrySolve(solver_factory(), answer)

def Exhaust(solver_factory):
  total_num_words = len(ALL_WORDS)
  failed = []
  guess_freq = defaultdict(int)  # Maps # of guesses to frequency.
  for i, answer in enumerate(ALL_WORDS):
    solver = solver_factory()
    num_guesses = TrySolve(solver, answer, show_process=False)
    guess_freq[num_guesses] += 1
    if not num_guesses:
      print(f'Failed to solve for answer {answer} (word {i} out of {total_num_words}).')
      failed.append(answer)

  # Print statistics.
  print(f'Tested {total_num_words} words.')
  for num_guesses in sorted(guess_freq.keys()):
    if num_guesses:
      prefix = f'{num_guesses} guesses'
    else:
      prefix = 'Failed'
    num_words = guess_freq[num_guesses]
    print(f'{prefix}: {num_words} words {num_words*100.0/total_num_words:.2f}%.')

def IsValidGuess(guess):
  if len(guess) != 5:
    return False
  for ch in guess:
    if not ch.isalpha():
      return False
  return True

def IsValidHints(hints):
  if len(hints) != 5:
    return False
  for hint in hints:
    if hint not in 'MOX':
      return False
  return True

def Solve(solver_factory):
  solver = solver_factory()
  for attempt in range(6):
    suggested_guess = solver.SuggestGuess()
    if not suggested_guess:
      print('Hmm, I ran out of ideas.')

    print(f'{len(solver.candidates)} words satisfy all hints so far.')
    while True:
      guess = input(
          f'What is your guess #{attempt + 1} (I suggest {suggested_guess})? '
          'Press <enter> to see all words that satisfy the existing hints. ').upper()
      if not guess:
        print('These words satisfy all hints so far:')
        print('\n'.join(sorted(solver.candidates)))
        continue
      if IsValidGuess(guess):
        break
      print('Invalid guess.  Please type again.')
    while True:
      hints = input('What are the hints you got (5-letter string, where M = match, '
                    'O = wrong order, X: not match)? ').upper()
      if IsValidHints(hints):
        break
      print('Invalid hints.  Please type again.')
    if hints == 'MMMMM':
      print(f'Success!  The answer is {FormatHints(guess, hints)}.')
      break
    print(f'Hint: {FormatHints(guess, hints)}')
    solver.MakeGuess(guess, hints)

def main():
  print('Welcome to Zhanyong Wan\'s Wordle Solver!\n')
  args = sys.argv[1:]
  # Valid choices:
  #   AudioLeftyWordleSolver,
  #   AudioWordleSolver,
  #   HardModeEagerWordleSolver,
  #   IgnoreEarliestHintsWordleSolver,
  #   TwoCoverWordleSolver
  solver_factory = TwoCoverWordleSolver
  if 'demo' in args:
    Demo(solver_factory)
  elif 'solve' in args:
    Solve(solver_factory)
  elif 'exhaust' in args:
    Exhaust(solver_factory)
  else:
    sys.exit(__doc__)

if __name__ == '__main__':
  main()
