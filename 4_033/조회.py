myInfo = {
    '이름':'홍길동',
    '전공':'컴공',
    '메일':'suhye4n@gmail.com',
    '학년':3,
    '주소':'서울시',
    '취미':['수영','축구']
}

print(myInfo['이름'])
print(myInfo['메일'])
print(myInfo['취미'])

print(myInfo.get('전공'))
print(myInfo.get('학년'))
print(myInfo.get('주소'))