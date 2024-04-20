nums = []

while len(nums) < 5:
    try:
        num = int(input('숫자를 입력하세요: '))
    except:
        print('정수를 입력하세요.')
        continue

    nums.append(num)


print(f'nums = {nums}')