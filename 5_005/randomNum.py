import random

def randomNumber():

    while True:
        n1 = random.randint(1,100)
        if n1 % 2 != 0:
            break

    return n1

print(randomNumber())