factorialDic = {}
for i in range(11):
    if i == 0:
        factorialDic[i] = 1
    else:
        for n in range(1, (i+1)):
            factorialDic[i] = factorialDic[i-1] * n
print(factorialDic)