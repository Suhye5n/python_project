n = 1

while n <= 101:
    if n % 2 == 0:
        print('{}은 2의 배수이다'.format(n))

    if n % 3 == 0:
        print('{}은 3의 배수이다'.format(n))
    n += 1