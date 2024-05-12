import random
nums = random.sample(range(50,100),20)
ranks = [0 for i in range(20)]

for idx, num1 in enumerate(nums):
    for num2 in nums:
        if num1 < num2:
            ranks[idx] += 1

print(f'nums: {nums}')
print(f'ranks: {ranks}')

for i, m in enumerate(nums):
    print(f'num: {m} \t rank: {ranks[i] + 1}')