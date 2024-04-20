num1 = 10
num2 = 100

numResult = True if num1 > num2 else False
print('num1 > num2 : {}'.format(numResult))


print('num1은 num2보다 크다.') if numResult else print('num1은 num2보다 크지 않다')