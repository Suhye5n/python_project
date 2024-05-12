scores = {'s1':8.9, 's2':8.1, 's3':8.5, 's4':9.8, 's5':8.8}
minScore = 10; minScoreKey = ''
maxScore = 0; maxScoreKey = ''

for key in scores.keys():

    if scores[key] < minScore:
        minScore = scores[key]
        minScoreKey = key

    if scores[key] > maxScore:
        maxScore = scores[key]
        maxScoreKey = key

print('minScore: {}'.format(minScore))
print('maxScore: {}'.format(maxScore))
print('minScoreKey: {}'.format(minScoreKey))
print('maxScoreKey: {}'.format(maxScoreKey))

del scores[minScoreKey]
del scores[maxScoreKey]

print('scores: {}'.format(scores))