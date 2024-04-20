
currentWeight = 800
date = 1

while True:
    if currentWeight >=2200:
        break

    date += 1
    currentWeight += 70

print('{}일차에 {}kg이므로 이유식을 중단합니다'.format(date, currentWeight))