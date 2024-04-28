#등비수열 공식: an = a1 * r*(n-1)

inputN1 = int(input('a1 입력: '))
inputR = int(input('공비 입력: '))
inputN = int(input('n 입력: '))

valueN = inputN1 * (inputR ** (inputN - 1))
print('{}번째 항의 값: {}'.format(inputN, valueN))