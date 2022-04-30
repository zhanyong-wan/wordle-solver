#!/usr/bin/env python3

from collections import defaultdict

import os

def GetWordList():
  py_file_dir = os.path.dirname(__file__)
  wordle_list_file = os.path.join(py_file_dir, '../wordle-list/words')
  words = []
  with open(wordle_list_file, 'r') as f:
    for line in f.readlines():
      word = line.strip().lower()
      if word:
        words.append(word)
  return words

def GetLetterFrequencies(words):
  letter_freq = defaultdict(int)
  for word in words:
    for letter in word:
      letter_freq[letter] += 1
  return letter_freq

def main():
  print('Welcome to Zhanyong Wan\'s Wordle Solver!')
  words = GetWordList()
  letter_freq = GetLetterFrequencies(words)
  print(f'{letter_freq}')

if __name__ == '__main__':
  main()
