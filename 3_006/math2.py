num1 = int(input('1보다 큰 정수 입력:'))
num2 = int(input('1보다 큰 정수 입력:'))

x = num1; y = num2

while y > 0:
    temp = y
    y = x % y
    x = temp

print('{}와 {}의 최대공약수: {}'.format(num1, num2, x))