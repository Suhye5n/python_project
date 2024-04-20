score = [int(input('국어 점수 입력: ')),
         int(input('영어 점수 입력: ')),
         int(input('수학 점수 입력: '))]

copyScores = score.copy()

for idx, score in enumerate(copyScores):
    result = score * 1.1
    copyScores[idx] = 100 if result > 100 else result
    #1.1배 한 점수가 100점이 넘으면 그 점수는 그냥 100으로 만들어줌
    #즉 점수의 최대치를 100으로 만들어주는 라인임

print(f'이전 평균: {round(sum(scores) / len(scores), 2)}')
print(f'이후 평균: {round(sum(copyScores) / len(copyScores), 2)}')