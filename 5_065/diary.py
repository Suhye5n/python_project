import time

def writeDiary(u, f, d):
    lt = time.localtime()
    timeStr = time.strftime('%Y-%m-%d %I:%M:%s %p', lt)

    filePath = u + f
    with open(filePath, 'a') as f:
        f.write(f'[{timeStr}] {d}\n')

def readDiary(u, f):
    filePath = u + f
    datas = []
    with open(filePath, 'r') as f:
        datas = f.readlines()

    return datas
