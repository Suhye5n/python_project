import datetime

today = datetime.datetime.today()
age = input('나이 입력: ')
if age.isdigit() :
    afterAge = 100 - int(age)
    year = today.year + afterAge
    print('{}년({}년후)에 100살!!'.format(year, afterAge))
else:
    print('숫자로 입력해주세요')
