
moneyCnt50000 = 0
moneyCnt10000 = 0
moneyCnt5000 = 0
moneyCnt1000 = 0
moneyCnt500 = 0
moneyCnt100 = 0
moneyCnt10 = 0

changeMoney = 0

productPrice = int(input('상품 가격 입력: '))
payPrice = int(input('지불 금액: '))

if payPrice > productPrice:
    changeMoney = payPrice - productPrice
    changeMoney = (changeMoney // 10) * 10
    print(changeMoney)

if changeMoney >= 50000 :
    moneyCnt50000 = changeMoney // 50000
    changeMoney %= 50000

if changeMoney >= 10000 :
    moneyCnt10000 = changeMoney // 10000
    changeMoney %= 10000

if changeMoney >= 5000 :
    moneyCnt5000 = changeMoney // 5000
    changeMoney %= 5000

if changeMoney >= 1000 :
    moneyCnt1000 = changeMoney // 1000
    changeMoney %= 1000

if changeMoney >= 500 :
    moneyCnt500 = changeMoney // 500
    changeMoney %= 500

if changeMoney >= 100 :
    moneyCnt100 = changeMoney // 100
    changeMoney %= 100

if changeMoney >= 10 :
    moneyCnt10 = changeMoney // 10
    changeMoney %= 10

print('50,000 {}장'.format(moneyCnt50000))
print('10,000 {}장'.format(moneyCnt10000))
print('5,000 {}장'.format(moneyCnt5000))
print('1,000 {}장'.format(moneyCnt1000))
print('500 {}장'.format(moneyCnt500))
print('100 {}장'.format(moneyCnt100))
print('10 {}장'.format(moneyCnt10))