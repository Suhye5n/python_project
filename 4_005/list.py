cars = ['그랜져','소나타','말리부','카니발','쏘렌토']

for i in range(len(cars)):
    print(cars[i])

for car in cars:
    print(car)

studentsCnts = [[1,19],[2,20],[3,22],[4,18],[5,21]]

for classNum, student in studentsCnts:
    print('{}학급 학생수: {}'.format(classNum,student))