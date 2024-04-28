inputN = int(input('n항 입력: '))

flag = True
n = 1; nCnt = 1; searchN = 0

while flag:

    for i in range(1, n+1):
        print('{}'.format(i), end = '')

        nCnt += 1
        if nCnt > inputN:
            searchN = i
            flag = False
            break #for문 빠져나오기

    print()
    n += 1


print('{}항: {}'.format(inputN, searchN))