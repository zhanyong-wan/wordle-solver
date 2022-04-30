#!/usr/bin/env python3

from collections import defaultdict

import os
import random

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

def Colored(r, g, b, text):
  return f'\033[38;2;{r};{g};{b}m{text}\033[38;2;255;255;255m'

def PrintHints(guess, hints):
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

def main():
  print('Welcome to Zhanyong Wan\'s Wordle Solver!')
  random.seed()
  words = GetWordList()
  answer = words[random.randrange(0, len(words))]
  sorted_word_weights = SortByLetterFrequencies(words)
  guess = sorted_word_weights[0][0]
  print(f'Guess #1: {guess}')
  hints = GetHints(guess, answer)
  print(f'Hint: {hints}')
  print(PrintHints(guess, hints))

if __name__ == '__main__':
  main()
