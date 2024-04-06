kor = int(input('국어점수: '))
eng = int(input('영어점수: '))
math = int(input('수학점수: '))

total = kor + eng + math
avgScore = total / 3
print('국어점수 :{}'.format(kor))
print('영어점수 :{}'.format(eng))
print('수학점수 :{}'.format(math))
print('평균점수 :%.1f' % avgScore)
