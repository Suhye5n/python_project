import operator

age = int(input('나이 입력 : '))

vaccine = operator.or_(operator.lt(age, 20),operator.ge(age,65))
print('age: {}, vaccine: {}'.format(age, vaccine))