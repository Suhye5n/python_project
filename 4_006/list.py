minScore = 60

scores = [['국어', 58],
          ['영어', 77],
          ['수학', 89],
          ['국사', 50],
          ['과학', 99]]

for item in scores:
    if item[1] < minScore:
        print('과락 과목: {}, 점수: {}'.format(item[0],item[1]))
for subject, score in scores:
    if score < minScore:
        print('과락 과목: {}, 점수: {}'.format(subject,score))