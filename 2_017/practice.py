rainAmount = 0
totalRainAmount = 0
month = 0

month += 1
totalRainAmount += 30
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 45
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 47
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 55
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 65
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 100
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 128
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 209
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 204
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 186
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 67
print(month,'월 누적 강수량 : ',totalRainAmount)

month += 1
totalRainAmount += 25
print(month,'월 누적 강수량 : ',format(totalRainAmount, ','))

avgRainAmount = totalRainAmount / 12

print('*'*30)
print('연간 누적 강수량 : {}mm'. format(totalRainAmount))
print('평균 강수량 : {}mm'. format(avgRainAmount))
print('*'*30)