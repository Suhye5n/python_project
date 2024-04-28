inputN = int(input('n 입력'))

result = 1
for n in range(1, (inputN + 1)):
    result *= n

print('{}팩토리얼: {}'.format(inputN, result))