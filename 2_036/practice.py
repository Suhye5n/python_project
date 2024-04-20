#팩토리얼을 실행할건데, result가 50이 넘을때의 숫자는 몇인지와 그때의 결과값을 구하기

result = 1
num = 0
for i in range(1, 11):
    result += i

    if result > 50:
        num = i
        break

print('num: {}, result: {}'.format(num, result))