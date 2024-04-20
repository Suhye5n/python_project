exampleScore = int(input('시험 성적 입력: '))
grades = ''

if exampleScore >= 90:
    grades = 'A'
elif exampleScore >= 80:
    grades = 'B'
elif exampleScore >= 70:
    grades = 'C'
elif exampleScore >= 60:
    grades = 'D'
else:
    grades = 'F'

print('성적 {} \t 학점: {}'.format(exampleScore, grades))