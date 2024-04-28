# an = {3, 7, 13, 21, 31, 43, 57}
# bn = {4, 6, 8, 10, 12, 14}

inputAN1 = int(input('a1 입력: '))
inputAN = int(input('a의 n 입력: '))

# inputBN1 = int(input('b1 입력: '))
# inputBD = int(input('b의 공차 입력: '))
#
# valueAN = 0
# valueBN = 0
#
# n = 1
# while n <= inputAN:
#
#     if n == 1:
#         valueAN = inputAN1
#         valueBN = inputBN1
#         print('an의 {}번째 항의 값: {}'.format(n, valueAN))
#         print('bn의 {}번째 항의 값: {}'.format(n, valueBN))
#         n += 1
#         continue
#
#     valueAN = valueAN + valueBN
#     valueBN = valueBN + inputBD
#     print('an의 {}번째 항의 값: {}'.format(n, valueAN))
#     print('bn의 {}번째 항의 값: {}'.format(n, valueBN))
#     n += 1


#n^2 + n + 1 = an
valueAN = inputAN ** 2 + inputAN + 1
print(valueAN)