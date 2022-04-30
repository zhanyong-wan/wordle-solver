# wordle-solver
A tool for solving the New York Times wordle puzzles in the hard mode.

## USAGE

```
wordle_solver.py demo
```
demonstrates solving a Wordle puzzle.

```
wordle_solver.py solve
```

helps you solve a Wordle puzzle (https://www.nytimes.com/games/wordle/index.html);
here's how it works:

1.  The tool tells you what you should guess next.
2.  You type the guess into the Wordle game.
3.  The game gives you hints based on the guess.
4.  You tell the tool what the hints are; for example, 'OMXXX' means that
    the first letter of the guess is in the answer but at a wrong spot,
    the second letter of the guess is in the answer and at the right spot,
    and the remaining letters of the guess are not in the answer.
5.  Repeat the above steps.

This tool's strategy conforms to the game's hard mode. I.e. it only makes
guesses that conform to all revealed hints.

Example session:

```
$ src/wordle_solver.py solve
Welcome to Zhanyong Wan's Wordle Solver!

Please type this as your guess #1: AROSE
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? OOXXX
Hint: AROSE
Please type this as your guess #2: LAIRY
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? MMXOX
Hint: LAIRY
Please type this as your guess #3: LARCH
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? MMMXX
Hint: LARCH
Please type this as your guess #4: LARUM
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? MMMXX
Hint: LARUM
Please type this as your guess #5: LARNT
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? MMMXX
Hint: LARNT
Please type this as your guess #6: LARVA
What are the hints you got (5-letter string, where M = match, O = wrong order, X: not match)? MMMMM
Success!  The answer is LARVA.
```