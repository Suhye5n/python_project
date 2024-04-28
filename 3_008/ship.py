ship1 = 3; ship2 = 4; ship3 = 5;
maxDay = 0

for i in range(1, (ship1 + 1)):
    if ship1 % i == 0 and ship2 % i == 0:
        maxDay = i

print('최대공약수: {}'.format(maxDay))

minDay = (ship1 * ship2) // maxDay
print('{}, {}의 최소공배수: {}'. format(ship1, ship2, minDay))

newDay = minDay

for i in range(1, (newDay + 1)):
    if ship1 % i == 0 and ship2 % i == 0:
        maxDay = i

print('최대공약수: {}'.format(maxDay))

minDay = (newDay * ship3) // maxDay
print('{}, {}, {}의 최소공배수: {}'.format(ship1, ship2, ship3, minDay))