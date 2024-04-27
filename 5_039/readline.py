uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

# with open(uri + 'lans.txt', 'r') as f:
#     lanList = f.readlines()
#
# print(f'lanList: {lanList}')
# print(f'lanList type: {type(lanList)}')
#

with open(uri + 'lans.txt', 'r') as f:
    line = f.readline()

    while line !='':
        print(f'line: {line}', end = '')
        line = f.readline()