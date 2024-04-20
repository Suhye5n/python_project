pi = 3.14
radius = float(input('반지름(cm) 입력: '))

circleArea = pi * radius * radius
circleLength = 2 * pi * radius

print('원의 넓이 \t : %dcm'%circleArea)
print('원 둘레길이 \t : %dcm'%circleArea)
print('원의 넓이 \t : %.1fcm'%circleArea)
print('원 둘레길이 \t : %.1fcm'%circleArea)
print('원의 넓이 \t : %.3fcm'%circleArea)
print('원 둘레길이 \t : %.3fcm'%circleArea)