numN = int(input('numN 입력: '))
numR = int(input('numR 입력: '))
result = 1

for n in range(numN, (numN-numR), -1):
    #이 경우에는 줄어드는 것이기 때문에 range의 뒷 숫자에 +1을 해주거나 하지 않아도 됨
    print('n: {}'.format(n))
    result = result * n

print('result: {}'.format(result))