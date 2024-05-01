class Member:

    def __init__(self, id, password):
        self.id = id
        self.pw = password

class MemberRepository:

    def __init__(self):
        self.members = {}

    def addMembers(self, m):
        self.members[m.id] = m.pw
        #위에서 .members에 딕셔너리를 만들고 [id] = 키값 이렇게 넣어준거

    def logIn(self, id, password):
        #받아야 하는 값을 적어줘야 함
        isMember = id in self.members
        #true 와 false 값으로 나옴

        if isMember and self.members[id] == password:
            #isMember가 true이고 거기 들어간 id 키값이 true이면
            print(f'{id}: log-in success!')
        else:
            print(f'{id}: log=in fail!!')

    def deleteMembers(self, i, p):
        del self.members[i]

    def printMembers(self):
        for mk in self.members.keys():
            #members의 키값들 이라는 뜻
            print(f'ID: {mk}')
            print(f'PW: {self.members[mk]}')
            #딕셔너리에서 mk의 id를 가진 키값(패스워드)를 호출해내는 것
