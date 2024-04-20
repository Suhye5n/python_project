minNum = 0

for i in range(1,101):
    if i % 3 != 0 or i % 7 != 0:
        continue

    print('공배수: {}'.format(i))

    if minNum == 0:
        minNum = i

else:
    print('최소 공배수: {}'.format(minNum))