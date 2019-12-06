# This is a sample program to demonstrate the capabilities of CRACKn's genetic algorithm combined with
# the Bandit static analysis tool
import random
import os

# somewhere higher in the code base a cryptographically safe random number generator is used
int.from_bytes(os.urandom(1), byteorder='big')

# unknown random function that is called by crypto_func
def foo(x):
    if x < 7:
        print('Secret crypto thing')
        return True
    return False

# represents a function that does cryptographic operations
def crypto_func():
    # represents a security vulnerability
    # cryptographic functions should not use pseudo-random number generators
    x = random.randint(-10, 10)
    foo(x)
    return x

# function to choose a random number for the user to guess
def get_number():
    # this call to a pseudo-random number generator is not a security vulnerability, but static analysis tools do not know this
    x = random.randint(1, 10)
    return x

# helper function to check if the user's guess was correct
# does not contain any security vulnerabilities
def guess(mystery, my_guess):
    if my_guess == mystery:
        print("You win!")
        return(True)
    else:
        print("Nope, guess again!")
        return(False)

# main loop of the game
def play_game(mystery):
    while(True):
        # the call to input represents a major security risk as input executes whatever is given as input as python code
        val = int(input())
        if guess(mystery, val):
            return(True)

# driver code
def main():
    print("I have picked a number between 1 and 10. Can you guess it?")
    mystery = get_number()
    play_game(mystery)
    