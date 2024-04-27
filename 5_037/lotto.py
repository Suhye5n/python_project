import random

uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

def writeNumbers(nums):
    for idx, num in enumerate(nums):
        with open(uri + 'lotto.txt', 'a') as f:
            if idx < len(nums) - 2:
                 f.write(str(num) + ', ')
            elif idx == len(nums) - 2:
                 f.write(str(num))
            elif idx == len(nums) - 1:
                f.write('\n')
                f.write('Bonus: ' + str(num))
                f.write('\n')

lNums = random.sample(range(1, 46), 7)
print(f'lnums: {lNums}')

writeNumbers(lNums)