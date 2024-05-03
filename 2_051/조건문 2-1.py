korAvg = 85; engAvg = 82; mathAvg = 89
sciAvg = 75; hisAvg = 94
totalAvg = korAvg + engAvg + mathAvg + sciAvg + hisAvg
avgAvg = int(totalAvg / 5)

korScore = int(input('국어 점수: '))
engScore = int(input('영어 점수: '))
mathScore = int(input('수학 점수: '))
sciScore = int(input('과학 점수: '))
hisScore = int(input('국사 점수: '))

totalScore = korScore + engScore + mathScore + sciScore + hisScore
avgScore = int(totalScore / 5)

korGap = korScore - korAvg
engGap = engScore - engAvg
mathGap = mathScore - mathAvg
sciGap = sciScore - sciAvg
hisGap = hisScore - hisAvg

totalGap = totalScore - totalAvg
avgGap = avgScore - avgAvg



print('-' * 70)
print('총점: {}({}), 평균: {}({}))'.format(totalScore, totalGap, avgScore, avgGap))
print('국어:{}({}), 영어:{}({}), 수학:{}({}), 과학:{}({}), 국사:{}({})'.format(
    korScore, korGap, engScore,engGap, mathScore, mathGap, sciScore, sciGap, hisScore, hisGap
))
print('-' * 70)
str = '+' if korGap > 0 else '-'
print('국어 편차: {}({})'.format(str * abs(korGap), korGap))
str = '+' if engGap > 0 else '-'
print('영어 편차: {}({})'.format(str * abs(engGap), engGap))
str = '+' if mathGap > 0 else '-'
print('수학 편차: {}({})'.format(str * abs(mathGap), mathGap))
str = '+' if sciGap > 0 else '-'
print('과학 편차: {}({})'.format(str * abs(sciGap), sciGap))
str = '+' if hisGap > 0 else '-'
print('국사 편차: {}({})'.format(str * abs(hisGap), hisGap))
print('-' * 70)
str = '+' if totalGap > 0 else '-'
print('총점 편차: {}({})'.format(str * abs(totalGap), totalGap))
str = '+' if avgGap > 0 else '-'
print('평균 편차: {}({})'.format(str * abs(avgGap), avgGap))
print('-' * 70)