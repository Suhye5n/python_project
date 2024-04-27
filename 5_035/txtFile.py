file = open('/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/time.txt', 'r')

str = file.read()
print(f'str : {str}')

file.close()