eveList = []; oddList = []; floatList = []

n = 1
while n < 6:
    try:
        num = float(input('input number: '))
    except:
        print('문자는 안돼요')
        print('Input number')
        continue
    else:
        if num - int(num) != 0:
            print('float number!')
            floatList.append(num)
        else:
            if num % 2 == 0:
                print('even number!')
                eveList.append(int(num))
            else:
                print('odd number!')
                oddList.append(int(num))

        n += 1

print(f'eveList: {eveList}')
print(f'oddList: {oddList}')
print(f'floatList: {floatList}')