import operator

num1 = 8
num2 = 3

print('{} + {} : {}'.format(num1, num2, operator.add(num1, num2)))
print('{} - {} : {}'.format(num1, num2, operator.sub(num1, num2)))
print('{} * {} : {}'.format(num1, num2, operator.mul(num1, num2)))
print('{} / {} : {}'.format(num1, num2, operator.truediv(num1, num2)))
print('{} % {} : {}'.format(num1, num2, operator.mod(num1, num2)))
print('{} // {} : {}'.format(num1, num2, operator.floordiv(num1, num2)))
print('{} ** {} : {}'.format(num1, num2, operator.pow(num1, num2)))