cars = ['그랜저', '소나타', '말리부', '카니발', '쏘렌토']

n = 0
while n < len(cars):
    print(cars[n])
    n += 1

n = 0
while True:
    print(cars[n])
    n += 1

    if n == len(cars):
        break

n = 0
flag = True
while flag:
    print(cars[n])
    n += 1

    if n == len(cars):
        flag = False