maxLength = 5200
maxWidth = 1985

myCarLength = int(input('전장 길이 입력 : '))
myCarWidth = int(input('전폭 길이 입력 : '))

print('전장 가능 여부: {}'.format(myCarLength <= maxLength))
print('전장 가능 여부: {}'.format(myCarLength <= maxWidth))