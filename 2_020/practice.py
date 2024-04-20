age = int(input('나이 입력 : '))

vaccine = (age < 20) or (age >= 65)
print('age: {}, vaccine: {}'.format(age, vaccine))