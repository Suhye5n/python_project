import random

types = ['A', 'B', 'AB', 'O']

todayData = []
typeCnt = []

for i in range(100):
    type = types[random.randrange(len(types))]
    #types 리스트의 길이만큼의 숫자에서 랜덤 숫자를 뽑아서 가져오고, 그걸 types의 인덱스에 받아서 결론적으로 랜덤한 type를 골라냄
    todayData.append(type)

print('todayData: {}'.format(todayData))
print('todayData length: {}'.format(len(todayData)))

for type in types:
    print('{}형 : {}개'.format(type, todayData.count(type)))