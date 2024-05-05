playerScores = [9.5, 8.9, 9.2, 9.8, 8.8, 9.0]
print('playerScores : {}'.format(playerScores))

minScore = 0; maxScore = 0
minScoreIdx = 0; maxScoreIdx = 0

for idx, score in enumerate(playerScores):
    if minScore > score or idx == 0:
        #이거는 처음이라는 조건을 안넣으면 minScore이 계속 0으로 유지되서 넣어줘야함
        minScoreIdx = idx
        minScore = score

print('minScore : {}, minScoreIdx: {}'.format(minScore, minScoreIdx))
playerScores.pop(minScoreIdx)

for idx, score in enumerate(playerScores):
    #여기는 idx == 0이라는 조건을 넣어줄 필요가 없음. 처음이라는 조건을 안넣어도 자동으로 최대값이 들어가니까
    if maxScore < score:
        maxScoreIdx = idx
        maxScore = score

print('maxScore : {}, maxScoreIdx : {}'.format(maxScore, maxScoreIdx))
playerScores.pop(maxScoreIdx)

print('playerScores : {}'.format(playerScores))