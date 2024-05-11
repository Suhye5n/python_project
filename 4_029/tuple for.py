studentCnts = (1, 19),(2, 20),(3, 22),(4, 18),(5, 21)
#튜플은 괄호 생략해도 됨. 현재 이중 튜플 상태임

for i in range(len(studentCnts)):
    print('{}학급 학생수: {}'.format(studentCnts[i][0], studentCnts[i][1]))

for classNo, cnt in studentCnts:
    print('{}학급 학생수: {}'.format(classNo, cnt))