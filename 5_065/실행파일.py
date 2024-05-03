import diary

members = {}
uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

def printMembers():
    for m in members.keys():
        print(f'ID:{m} \t PW{members[m]}')

while True:
    selectNum = int(input('1.회원가입 2.한줄 일기쓰기 3.일기보기 4.종료'))

    if selectNum == 1:
        mId = input('input ID: ')
        mPw = input('input PW: ')
        members[mId] = mPw
        printMembers()

    elif selectNum == 2:
        mId = input('input ID: ')
        mPw = input('input PW: ')

        if mId in members and mPw == members[mId]:
            print('login success!!')
            fileName = 'myDiary_' + mId + '.txt'
            data = input('오늘 하루 인상깊은 일을 입력하세요')
            diary.writeDiary(uri, fileName, data)

        else:
            print('login fail!!')
            printMembers()

    elif selectNum == 3:
        mId = input('input ID: ')
        mPw = input('input PW: ')

        if mId in members and mPw == members[mId]:
            print('login success!!')
            fileName = 'myDiary_' + mId + '.txt'
            datas = diary.readDiary(uri, fileName)
            for d in datas:
                print(d, end = '')


        else:
            print('login fail!!')
            printMembers()

    elif selectNum == 4:
        print('Bye!')
        break