import time

lt = time.localtime()

# dateStr = '[' + str(lt.tm_year) + '년 ' +\
#           '' + str(lt.tm_mon) + '월 ' + str(lt.tm_mday) + '일] '

dateStr = '[' + time.strftime('%Y-%m-%d %I:%M:%S %p') + ']'

todaySchedule = input('오늘 일정: ')

file = open('/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/time.txt', 'w')
file.write(dateStr + todaySchedule)
file.close()
