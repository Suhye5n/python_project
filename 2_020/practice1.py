passScore1 = 60
passScore2 = 70

korScore = int(input('국어 점수: '))
engScore = int(input('영어 점수: '))
mathScore = int(input('수학 점수: '))

avgScore = (korScore + engScore + mathScore) / 3
aveScoreResult = avgScore >= passScore2

korResult = korScore >= passScore1
engResult = engScore >= passScore1
mathResult = mathScore >= passScore1

subjectResult = korResult and engResult and mathResult

print('평균 : {}, 결과 : {}'.format(avgScore, aveScoreResult))

print('국어 : {}, 결과 : {}'.format(korScore, korResult))
print('영어 : {}, 결과 : {}'.format(engScore, engResult))
print('수학 : {}, 결과 : {}'.format(mathScore, mathResult))
print('과락 결과 : {}'.format(subjectResult))

print('최종 결과 : {}'.format(avgScore and subjectResult))