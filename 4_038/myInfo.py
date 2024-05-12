myInfo = {
    '이름':'ohsuhyeun',
    '나이':'39',
    '연락처':'01073767020',
    '주민등록번호':'970201-22222222',
    '주소':'서울시 관악구 봉천로'
}
print(myInfo)

deleteItem = ['연락처','주민등록번호']

for item in deleteItem:
    if item in myInfo:
        del myInfo[item]

print(myInfo)