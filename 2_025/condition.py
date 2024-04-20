rainPercentage = int(input('비 올 확률 입력: '))
minRainPercentage = 55

print('우산 챙기세요') if rainPercentage >= minRainPercentage else print('양산 챙기세요')

if rainPercentage >= minRainPercentage:
    print('우산 챙기세요')
else:
    print('양산 챙기세요')