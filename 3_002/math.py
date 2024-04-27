inputNumber = int(input('0보다 큰 정수 입력'))

for number in range(1, inputNumber + 1):
    if inputNumber % number == 0:
        print('{}의 약수: {}'.format(inputNumber, number))