korScore = int(input('국어 점수 입력: '))
engScore = int(input('영어 점수 입력: '))
mathScore = int(input('수학 점수 입력: '))

totalScore = korScore + engScore + mathScore
avgScore = totalScore / 3

maxScore = korScore
maxSubject = '국어'
if engScore > maxScore:
    maxScore = engScore
    maxSubject = '영어'

if mathScore > maxScore:
    maxScore = mathScore
    maxSubject = '수학'