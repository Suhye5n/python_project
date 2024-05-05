def add(n, m):
    return n + m

def sub(n, m):
    return n - m

def mul(n, m):
    return n * m

def div(n, m):
    return n / m

def mod(n, m):
    return n % m

def flo(n, m):
    return n // m

def exp(n, m):
    return n ** m

while True:
    print('-'*60)
    selectNum = int(input('1. 덧셈  2. 뺄셈  3. 곱셈  4. 나눗셈  5. 나머지  6. 몫  7. 거듭제곱  8. 종료'))
    if selectNum == 8:
        print('Bye')
        break

    num1 = float(input('첫 번째 숫자 입력: '))
    num2 = float(input('두 번째 숫자 입력: '))

    if selectNum == 1:
        print(f'{num1} + {num2} = {add(num1, num2)}')
    elif selectNum == 2:
        print(f'{num1} - {num2} = {sub(num1, num2)}')
    elif selectNum == 3:
        print(f'{num1} * {num2} = {mul(num1, num2)}')
    elif selectNum == 4:
        print(f'{num1} / {num2} = {div(num1, num2)}')
    elif selectNum == 5:
        print(f'{num1} % {num2} = {mod(num1, num2)}')
    elif selectNum == 6:
        print(f'{num1} // {num2} = {flo(num1, num2)}')
    elif selectNum == 7:
        print(f'{num1} ** {num2} = {exp(num1, num2)}')

    else:
        print('잘못 입력하셨습니다. 다시 입력하세요.')

    print('-' * 60)