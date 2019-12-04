import random

def get_number():
    x = 5
    x = random.randint(1, 10)
    return x

def guess(mystery, my_guess):
    if my_guess == mystery:
        print("You win!")
        return(True)
    else:
        print("Nope, guess again!")
        return(False)

def play_game(mystery):
    while(True):
        val = int(input())
        if guess(mystery, val):
            return(True)

def main():
    print("I have picked a number between 1 and 10. Can you guess it?")
    mystery = get_number()
    play_game(mystery)
    