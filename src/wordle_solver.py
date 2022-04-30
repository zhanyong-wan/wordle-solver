#!/usr/bin/env python3

"""New York Times Wordle Puzzle Solver.

USAGE

    wordle_solver.py demo
      demonstrates solving a Wordle puzzle.

    wordle_solver.py resolve
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

def GetLetterFrequencies(words):
  letter_freq = defaultdict(int)
  for word in words:
    for letter in word:
      letter_freq[letter] += 1
  return letter_freq

def SortByLetterFrequencies(words):
  letter_freq = GetLetterFrequencies(words)
  word_weights = []
  for word in words:
    weight = sum(letter_freq[ch] for ch in set(word))
    word_weights.append((word, weight))
  return sorted(word_weights, key=lambda word_weight: word_weight[1], reverse=True)

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

def Demo():
  random.seed()
  words = GetWordList()
  answer = words[random.randrange(0, len(words))]
  for attempt in range(6):
    sorted_word_weights = SortByLetterFrequencies(words)
    if not sorted_word_weights:
      print('Hmm, I ran out of ideas.')
      break
    guess = sorted_word_weights[0][0]
    print(f'Guess #{attempt +1}: {guess}')
    hints = GetHints(guess, answer)
    if hints == 'MMMMM':
      print(f'Success!  The answer is {FormatHints(guess, hints)}.')
      break
    print(f'Hint: {FormatHints(guess, hints)}')
    words = FilterByHints(words, guess, hints)

def IsValidHints(hints):
  if len(hints) != 5:
    return False
  for hint in hints:
    if hint not in 'MOX':
      return False
  return True

def Solve():
  words = GetWordList()
  for attempt in range(6):
    sorted_word_weights = SortByLetterFrequencies(words)
    if not sorted_word_weights:
      print('Hmm, I ran out of ideas.')
      break

    guess = sorted_word_weights[0][0]
    print(f'Please type this as your guess #{attempt +1}: {guess}')
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

    words = FilterByHints(words, guess, hints)

def main():
  print('Welcome to Zhanyong Wan\'s Wordle Solver!\n')
  args = sys.argv[1:]
  if 'demo' in args:
    Demo()
  elif 'solve' in args:
    Solve()
  else:
    sys.exit(__doc__)

if __name__ == '__main__':
  main()
