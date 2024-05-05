sports = ['농구','수구','축구','마라톤','테니스']
favoriteSport = input('가장 좋아하는 스포츠 입력: ')
bestSportID = 0

for id, value in enumerate(sports):
    if value == favoriteSport:
        bestSportID = id + 1

print('{}은 {}번째에 있습니다.'.format(sports, bestSportID))