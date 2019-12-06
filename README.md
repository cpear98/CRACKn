# CRACKn
## Introduction
CRACKn is an experimental tool which attempts to achieve automatic program repair of Python source code with respect to security vulnerabilities by leveraging static analysis tools and a genetic algorithm engine to make mutations to the source code.

## Setup
This project is built using Python 3 and relies on the static analysis tool [Bandit](https://pypi.org/project/bandit/). Make sure you have a working version of Python 3 installed on your system before continuing with setup. In order to automatically install all dependencies you can run the command

`$ sudo pip3 install -r requirements.txt` 

from the main project directory. If you don't want to install these dependencies globally you can alternatively create a virtual environment to run the project in. This can be accomplished with the following commands, all run from the project's main directory:

```
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
```

## Running CRACKn
To run CRACKn you must place a project in the `repos` directory. Repo directories have the following structure:

```
repos
  - [repo_name]
    - __init__.py
    - src
      - __init__.py
      - [source_file].py
    - test
      - __init__.py
      - test_[source_file].py
```

You can look at the `example1` repo provided for reference.

To get our feet wet with CRACKn we will quickly run the tool on the provided example repo. To invoke the tool type in the command 

`python3 src/main.py repo=example1`

This tells CRACKn to run the tool on the `example1` folder in the repos directory. CRACKn will now begin simulating for several generations, which can take several minutes. When it is finished, it will create a new directory in the `example1` repo called `results` which contains a new file `guessing_game_mutated.py`. Compare this to the original `guessing_game.py` in the `example1/src` directory and see if you can find the mutations! CRACKn is nowhere near finished and may not correctly mutate the source code to both preserve functionality and fix all vulnerabilities, but it will attempt to make mutations which decrease the number and severity of the vulnerabilities found by the Bandit static analyzer, as well as minimize the functional changes with respect to a provided test suite (you can look at `guessing_game.py`'s rather weak test suite in `example1/test/test_guessing_game.py`).

## Changing CRACKn's Mode of Operation
Currently CRACKn will mutate any repo given to it for exactly 10 generations. This is becuase the tool is currently set to operate in "Set Generations" mode, where it is given a number of generations and it executes for exactly that many generations. Currently this is the prefered mode due to its slow, unoptimized state. In the future, you will be able to change the number of generations or the operation mode via command line arguments, but this functionality is not currently avialable. Instead, let's make these changes by going into CRACKn's source code. Open the file `main.py` in the `src` folder. At the very bottom of the file there is a line that reads

`simulator.sim_n_generation(10)`

We can change the number of generations that CRACKn will simulate for by changing the number 10 to a different integer. Just keep in mind that large values will cause the simulation to run for a very long time!

Alternately we can change the mode of operation to "Sim Until Optimal" mode by changing this line to

`simulator.sim_until_optimal_found()`

In this mode, CRACKn will attempt to continue simulating until it finds an optimal solution (a mutation of the original source code that contains no security vulnerabilities and does not fail any of its test cases). It will also check if it has not been making progress for a very long time and try to reset itself, or shut down after many generations with no optimal solution found. Feel free to experiment with this mode of operation, but it is currently in progress and has not been verified to be functionally correct.

## Known Limitations, Bugs, and Issues
Here are listed several known issues with the CRACKn tool at a high level to look out for. CRACKn is a highly experimental reasearch tool which is still in its early days of development, so many of these issues should hopefully be ironed out in upcoming patches!

- Only works for single file programs
- Only works with the unittest testing framework
- Does not crash gracefully. If the program crashes mid-execution or is interupted by the user it may not clean up all of its temporary files
- Has not been verified to terminate gracefully on very large generation counts
- Unoptimized and very slow!
- Currently does not produce *final* results. Only intermediate mutations.
