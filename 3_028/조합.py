numN = int(input('numN 입력: '))
numR = int(input('numR 입력: '))

resultP = 1
resultR = 1
resultC = 1

for n in range(numN, (numN - numR), -1):
    print('n : {}'.format(n))
    resultP = resultP * n

print('resultP : {}'.format(resultP))

for n in range(numR, 0, -1):
    print('n : {}'.format(n))
    resultR = resultR * n

print('resultR : {}'.format(resultR))

resultC = int(resultP / resultR)
print('resultC : {}'.format(resultC))

result = (1/resultC) * 100
print(result)