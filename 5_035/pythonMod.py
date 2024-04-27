file = open('/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/python.txt', 'r', encoding='UTF8')

str = file.read()
print(f'str : {str}')

file.close()

str = str.replace('Python', '파이썬', 2)
print(f'str : {str}')

