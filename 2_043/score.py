midScore = input('중간 고사 점수: ')
finScore = input('기말 고사 점수: ')

if midScore.isdigit() and finScore.isdigit():
    midScore = int(midScore)
    finScore = int(finScore)
    sumScore = midScore + finScore
    print('총점: {}, 평균: {}'.format(sumScore, sumScore / 2))
else:
    print('잘못 입력했습니다.')

