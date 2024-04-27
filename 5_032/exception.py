num1 = int(input('input number1: '))
num2 = int(input('input number2: '))

try:
    print(f'num1 / num2 = {num1 / num2}')
except Exception as e:
    print(e)

print(f'num1 * num2 = {num1 * num2}')
print(f'num1 - num2 = {num1 - num2}')
print(f'num1 + num2 = {num1 + num2}')