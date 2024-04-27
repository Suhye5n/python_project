inputNumber = int(input('1보다 큰 정수 입력:'))

n = 2
while n <= inputNumber:
    if inputNumber % n == 0:
        print('소인수: {}'.format(n) )
        inputNumber = inputNumber / n
    else:
        n += 1