import member as mb
#같은 폴더에서 member 이라는 이름을 가진 파일을 mb라는 이름으로 가져오겠다.

mems = mb.MemberRepository()
#객체를 mems라는 변수에 담아줌.즉 그냥 class 자체를 담아준거임

for i in range(3):
    mID = input('아이디 입력: ')
    mPW = input('비밀번호 입력: ')
    mem = mb.Member(mID, mPW)
    #mem이라는 변수에 클래스 Members를 사용해 ID, Password를 담아줌
    mems.addMembers(mem)
    #MemerRepository 클래스의 addMembers 기능을 사용한 것

mems.printMembers()

mems.logIn('abc@gmail.com','1234')
mems.logIn('def@gmail.com','5678')
mems.logIn('ghi@gmail.com','9721')

mems.deleteMembers('abc@gmail.com', '1234')

mems.printMembers()