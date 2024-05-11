studentsTuple = ('홍길동', '박찬호', '이용규', '박승철', '김지은')

print('studentsTuple: {}'.format(studentsTuple))


searchName = input('학생 이름 입력: ')

if searchName in studentsTuple:
    print('{} 학생은 우리반 학생입니다.'.format(searchName))
else:
    print('{} 학생은 우리반 학생이 아닙니다.'.format(searchName))