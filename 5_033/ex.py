class PasswordLengthShortException(Exception):

    def __init__(self, str):
        super().__init__(f'{str}: 길이 5 미만')

class PasswordLengthLongException(Exception):

    def __init__(self, str):
        super().__init__(f'{str}: 길이 10 초과')

class PasswordWrongException(Exception):

    def __init__(self, str):
        super().__init__(f'{str}: 잘못된 비밀번호')

adminPw = input('input admin password: ')

try:
    if len(adminPw) < 5:
        raise PasswordLengthShortException(adminPw)
    elif len(adminPw) > 10:
        raise PasswordLengthLongException(adminPw)
    elif adminPw != 'admin1234':
        raise PasswordWrongException(adminPw)
    elif adminPw == 'admin1234':
        print('빙고!!')
except PasswordLengthShortException as e1:
    print(e1)

except PasswordLengthLongException as e2:
    print(e2)

except PasswordWrongException as e3:
    print(e3)