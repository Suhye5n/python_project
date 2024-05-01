message = input('메세지 입력: ')
lenMessage = len(message)
msgPrice = 50

if lenMessage <= 50:
    msgPrice = 50
    print('SMS 발송!!')


else:
    msgPrice = 100
    print('MMS 발송!!')

print('메세지 길이: {}'.format(lenMessage))
print('메세지 발송 요금: {}'.format(msgPrice))