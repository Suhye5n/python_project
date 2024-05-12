scores = {'kor':88, 'eng':55, 'math':85, 'sci':57, 'his':82}
print(f'scores : {scores}')

minScore = 60
fValue = 'F(재시험)'
fDic = {}

for key in scores.keys():
    if scores[key] < minScore:
        scores[key] = fValue
        fDic[key] = fValue

print(f'scores: {scores}')
print(f'fDic: {fDic}')