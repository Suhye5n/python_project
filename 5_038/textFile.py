languages = ['c/c++', 'java', 'c#', 'python', 'javascript']

uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'
# for item in languages:
#     with open(uri + 'languges.txt', 'a') as f:
#         f.write(item)
#         f.write('\n')

# with open(uri + 'languages.txt', 'a') as f:
#     f.writelines(item + '\n' for item in languages)

with open(uri + 'languges.txt', 'r') as f:
    print(f.read())