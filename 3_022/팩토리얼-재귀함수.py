inputN = int(input('n 입력: '))

def factorialFun(n):
    if n == 1:
         return 1

    return n * factorialFun(n-1)

print('{}팩토리얼: {}'.format(inputN, factorialFun(inputN)))