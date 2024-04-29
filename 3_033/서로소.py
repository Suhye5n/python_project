import random

rNum1 = random.randint(100, 1000)
rNum2 = random.randint(100, 1000)

print(f'rNum1: {rNum1}')
print(f'rNum2: {rNum2}')

for n in range(1, (min(rNum1, rNum2)+1)):
    if rNum1 % n == 0 and rNum2 % n == 0:
        print(f'공약수: {n}')
        maxNum = n

print(f'최대공약수: {maxNum}')

if maxNum == 1:
    print(f'{rNum1}과 {rNum2}는 서로소이다.')