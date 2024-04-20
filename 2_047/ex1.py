hou = int(input('시간 입력: '))
min = int(input('분 입력: '))
sec = int(input('초 입력: '))


print('{}초'.format(format(hou * 60 * 60 + min * 60 + sec , ',')))