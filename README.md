# wordle-solver
A perfect solver for the New York Times wordle puzzles.  This tool can solve all
wordle puzzles within 6 guesses.

## USAGE

```
wordle_solver.py webdemo
```

demonstrates solving a Wordle puzzle on the NYT website; this requires
Chrome, selenium, and webdriver-manager to be installed.

```
wordle_solver.py demo
```
demonstrates solving a Wordle puzzle locally.

```
wordle_solver.py solve
```

helps you solve a Wordle puzzle (https://www.nytimes.com/games/wordle/index.html.

### webdemo

Before running the `webdemo` command, you need to set up your machine to
allow Python to interact with an existing Chrome session:

```
pip install selenium
pip install webdriver-manager
```

Then, add the following lines to `~/.bash_profile`:

```
# Set up for running Chrome from the command line.
export PATH="/Applications/Google Chrome.app/Contents/MacOS:$PATH"
alias chrome-for-wordle='Google\ Chrome --remote-debugging-port=9222 --user-data-dir="~/WordleChromeProfile"'
```

Then run:

```
source ~/.bash_profile
mkdir ~/WordleChromeProfile
chrome-for-wordle
```

A new Chrome window should open.  The tool will use this window to play the game.
To start auto-playing, run this in another shell window:

```
wordle-solver/src/wordle_solver webdemo
```

The tool will repeatedly play the game (once an hour).  Therefore if you let it
run for multiple days, you'll get a winning streak.  However, if the work is
interrupted somehow (e.g. the tool crashed, the Chrome window is closed, the
machine is restarted, etc), you can resume playing without losing the winning
history, by

```
# Start chrome.
chrome-for-wordle
# In another shell window, start the tool:
wordle-solver/src/wordle_solver webdemo
```

### solve

Here's how `solve` works:

1.  The tool tells you what you should guess next.
2.  You type the guess into the Wordle game.
3.  The game gives you hints based on the guess.
4.  You tell the tool what the hints are; for example, 'OMXXX' means that
    the first letter of the guess is in the answer but at a wrong spot,
    the second letter of the guess is in the answer and at the right spot,
    and the remaining letters of the guess are not in the answer.
5.  Repeat the above steps.

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

## Implementation notes

The valid answers and valid guesses are obtained from the game's source code:

1.  Go to the game (https://www.nytimes.com/games/wordle/index.html).
1.  Right click on the background, View Page Source.
1.  Find the reference to the source script.  It looks like
    `<script src="main.5d21d0d0.js"></script>`.
1.  Open the `.js` file.  Find two lists in it:
    *   `var ko=["cigar","rebut",...]` is the list of valid answers.
    *   `wo=["aahed","aalii",...]` is the list of valid guesses.  This is
        disjoint with the previous list, so the actual valid guesses are
        the union of the two lists.