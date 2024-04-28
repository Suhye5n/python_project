inputN = int(input('n 입력: '))

valueN = 0
sumN = 0
valuePreN2 = 0
valuePreN1 = 0

n = 1
while n <= inputN:
    if n == 1 or n == 2:
        valueN = 1
        valuePreN2 = valueN
        valuePreN1 = valueN
#여기 코드 뭐가 잘못됐는데 그냥 넘어간다...
        sumN += valueN
        n += 1

    else:
        valueN = valuePreN2 + valuePreN1
        valuePreN2 = valuePreN1
        valuePreN1 = valueN
#N1-N2-N1-N1-N1-N1 이렇게 3번째부터는 N1에 있는 값이 들어간다고 생각하면 됨
        sumN += valueN
        n += 1

print('{}번째 항의 값: {}'.format(inputN, valueN))
print('{}번째 항까지의 합: {}'.format(inputN, sumN))