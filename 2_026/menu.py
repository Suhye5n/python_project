print('1.카페라떼(3.5) \t 2.에스프레소(3.0) \t 3.아메리카노(2.0) \t 4.곡물라떼(4.0) \t 5.밀크티(4.3)')
userSelectNumber = int(input('메뉴 선택: '))

if userSelectNumber == 1:
    print('-'*20+'\n메뉴 : 카페라떼\n가격 : 3,500원\n'+'-'*20)
elif userSelectNumber == 2:
    print('-'*20+'\n메뉴 : 에스프레소\n가격 : 3,000원\n'+'-'*20)
elif userSelectNumber == 3:
    print('-' * 20 + '\n메뉴 : 아메리카노\n가격 : 2,000원\n' + '-' * 20)
elif userSelectNumber == 4:
    print('-' * 20 + '\n메뉴 : 곡물라떼\n가격 : 4,000원\n' + '-' * 20)
else:
    print('-'*20+'\n메뉴 : 밀크티\n가격 : 4,300원\n'+'-'*20)
