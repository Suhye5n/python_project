#sn = n(a1 + an) / 2
#an = a1 + (n-1)d

inputN1 = int(input('a1 입력: '))
inputD = int(input('곧차 입력: '))
inputN = int(input('n 입력: '))

valueN = inputN1 + (inputN - 1) * inputD
sumN = inputN * (inputN1 + valueN) / 2
print('{}번째 항까지의 합: {}'.format(inputN, int(sumN)))