uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

#'w'파일 모드
file = open(uri + 'hello.txt', 'w')
file.write('Hello python!!')
file.close()

#'a'파일 모드
file = open(uri + 'hello.txt', 'a')
file.write('\n Hello world!!')
file.close()

#'a'파일 모드
file = open(uri + 'hello_03.txt', 'x')
file.write('Hello world!!')
file.close()

#'r'파일 모드
file = open(uri + 'hello_02.txt', 'r')
str = file.read()
print(f'str: {str}')
file.close()
