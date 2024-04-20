def calculator(n1, n2, operator):

    def addCal():
        print(f'덧셈 연산: {n1 + n2}')
    def subCal():
        print(f'뺄셈 연산: {n1 - n2}')
    def mulCal():
        print(f'곱셈 연산: {n1 * n2}')
    def divCal():
        print(f'나눗셈 연산: {n1 / n2}')

    if operator == 1:
        addCal()
    elif operator == 2:
        subCal()
    elif operator == 3:
        mulCal()
    elif operator == 4:
        divCal()

while True:
    num1 = float(input('실수(n1) 입력: '))
    num2 = float(input('실수(n2) 입력: '))
    operatorNum = int(input('1.덧셈, 2.뺄셈, 3.곱셈, 4.나눗셈, 5,종료'))

    if operatorNum == 5:
        print("bye!")
        break

    calculator(num1, num2, operatorNum)