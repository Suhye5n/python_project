inputN1 = int(input('a1 입력: '))
inputD = int(input('공차 입력: '))
inputN = int(input('n 입력: '))

valueN = 0
n = 1
while n <= inputN:

    if n == 1:
        valueN = inputN1
        print('{}번째 항의 값 : {}'.format(n, valueN))
        n += 1
        continue

    valueN = valueN + inputD
    print('{}번째 항의 값: {}'.format(n, valueN))
    n += 1

