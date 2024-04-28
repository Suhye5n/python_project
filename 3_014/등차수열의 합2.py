#an = a1 + (n-1)d
#sn = n(a1 + an) / 2

inputN1 = int(input('a1 입력: '))
inputD = int(input('공차 입력: '))
inputN = int(input('n 입력: '))

valueN = inputN + (inputN - 1) * inputD
sumN = inputN * (inputN1 + valueN) / 2

print('{}번째 합까지의 값: {}'.format(inputN, int(sumN)))