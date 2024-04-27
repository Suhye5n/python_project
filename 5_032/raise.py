def divCalculator(n1, n2):

    if n2 != 0:
        print(f'{n1} / {n2} = {n1 / n2}')

    else:
        raise Exception('0으로 나눌 수 없습니다!')

num1 = int(input('inputnumber1 : '))
num2 = int(input('inputnumber2 : '))

try:
    divCalculator(num1, num2)

except Exception as e:
    print(f'Exception: {e}')