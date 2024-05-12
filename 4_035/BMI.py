myBodyInfo = {'이름':'suhyeon','몸무게':48, '신장':1.6}
myBMI = myBodyInfo['몸무게'] / (myBodyInfo['신장'] ** 2)
print(f'myBodyInfo: {myBodyInfo}')
print(f'myBMI: {round(myBMI, 2)}')

date = 0
while True:
    date += 1

    myBodyInfo['몸무게'] = round(myBodyInfo['몸무게'] - 0.3, 2)
    print(f'몸무게: {myBodyInfo['몸무게']}')

    myBodyInfo['신장'] = round(myBodyInfo['신장'] + 0.001, 3)
    print(f'신장: {myBodyInfo['신장']}')

    myBMI = myBodyInfo['몸무게'] / (myBodyInfo['신장'] ** 2)
    print(f'BMI: {round(myBMI,2)}')

    if date >= 30:
        break