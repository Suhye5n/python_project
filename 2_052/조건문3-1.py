import random

comNum = random.randint(1, 2)
userSelect = int(input(('홀/짝 선택: 1.홀수 2.짝수')))


if comNum == 1 and userSelect == 1:
    print('빙고!! 홀수!!')

elif comNum == 2 and userSelect == 2:
    print('빙고!! 짝수!!')

elif comNum == 1 and userSelect == 2:
    print('실패!! 홀수!!')

elif comNum == 2 and userSelect == 1:
    print('실패!! 짝수!!')