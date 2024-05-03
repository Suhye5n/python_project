import random

comNumber = random.randint(1, 3)
userNumber = int(input('가위, 바위, 보 선택:  1. 가위 \t 2. 바위\t 3. 보'))

if ((comNumber == 1 and userNumber == 2) or
        (comNumber == 2 and userNumber == 3) or
        (comNumber == 3 and userNumber == 1)):
    print('컴퓨터: 패, 유저: 승')

elif comNumber == userNumber :
    print('무승부')

else:
    print('컴퓨터: 승, 유저: 패')

print('컴퓨터: {}, 유저: {}'.format(comNumber, userNumber))