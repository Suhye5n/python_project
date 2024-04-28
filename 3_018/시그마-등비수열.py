#sn = a1 * (1 - r^n) / (1 - r)
inputN1 = int(input('a1 입력: '))
inputR = int(input('곧비 입력: '))
inputN = int(input('n 입력: '))

sumN = inputN1 * (1 - (inputR ** inputN)) / (1 - inputR)
print('{}번째 항까지의 합: {}'.format(inputN, int(sumN)))