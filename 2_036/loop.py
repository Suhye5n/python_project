# num = 0
#
# while True:
#     print('Hello')
#
#     num += 1
#
#     if num >= 5:
#         break
#
# print('The End!')

sum = 0
searchNum = 0

for i in range(100):
    sum += i

    if sum > 100:
        searchNum = i
        break

print('searchNum : {}'.format(searchNum))
