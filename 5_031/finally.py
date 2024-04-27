eveList = []; oddList = []; floatList = []; dataList = []
n = 1

while n < 6 :
    try:
        inputData = input('input number: ')
        numFlo = float(inputData)
    except:
        print('exception raise!!')
        print('input number again!!')
        continue

    else:
        numInt = int(numFlo)
        if numFlo - numInt != 0:
            floatList.append(numFlo)
            print('float number!!')

        elif numInt % 2 == 0:
            eveList.append(numInt)
            print('even number!!')

        else:
            oddList.append(numInt)
            print('odd number')

    finally:
        dataList.append(inputData)
        n += 1

print(f'eveList: {eveList}')
print(f'oddList: {oddList}')
print(f'floatList: {floatList}')
print(f'dataList: {dataList}')