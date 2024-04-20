limitSnow = 30
snowAmount = int(input('적설량 입력(mm) : '))

print('적설량: {}mm, {}'.format(snowAmount, '대설 경보 발령')) if limitSnow <= snowAmount else\
    print('적설량: {}mm, {}'.format(snowAmount, '대설 경보 해제'))