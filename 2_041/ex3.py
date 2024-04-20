width = float(input('가로길이 입력: '))
height = float(input('세로길이 입력: '))

triangleArea = width * height / 2
squareArea = width * height

print('-' * 25)
print('삼각형 넓이 : %.2f '%triangleArea)
print('사각형 넓이 : %.2f '%squareArea)
print('-' * 25)