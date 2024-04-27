uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

scoreDic = {}
with open(uri + 'scorelist.txt', 'r') as f:
    line = f.readline()

    while line != '':
        tempList = line.split(':')
        scoreDic[tempList[0]] = int(tempList[1].strip('\n'))
        line = f.readline()

print(scoreDic)