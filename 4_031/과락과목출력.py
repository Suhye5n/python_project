minScore = 60

scores = (
    ('국어', 58),
    ('영어', 77),
    ('수학', 89),
    ('과학', 99),
    ('국사', 50)
)

n = 0
while n < len(scores):
    if scores[n][1] < minScore:
        print('과락과목 : {}, 점수 : {}'.format(scores[n][0],scores[n][1]))

    n += 1


n = 0
while n < len(scores):
    if scores[n][1] >= minScore:
        continue

    print('과락과목 : {}, 점수 : {}'.format(scores[n][0],scores[n][1]))
    n += 1