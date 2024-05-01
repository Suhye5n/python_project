class NormalTV:

    def __init__(self, i=32, c='black', r='full-HD'):
        #i, c, r의 기본 설정을 만들어 준거임
        self.inch = i
        #여기서 i에 다른값이 들어오면 32에서 다른 값으로 i가 변경될 수 있음
        self.color = c
        self.resolution = r
        self.smartTV = 'off'
        self.aiTV = 'off'

    def turnOn(self):
        print('TV power on!!')

    def turnOff(self):
        print('TV power off!!')

    def printTvInfo(self):
        print(f'inch: {self.inch}inch')
        print(f'color: {self.color}')
        print(f'resolution: {self.resolution}')
        print(f'smartTV: {self.smartTV}')
        print(f'aiTV: {self.aiTV}')


class Tv4k(NormalTV):

    def __init__(self,i, c, r = '4k'):
        super().__init__(i, c, r)
        #super()는 상위 클래스에 받은 i,c,r을 다 올려줌

    def setSmartTV(self,s):
        self.smartTV = s


class Tv8k(NormalTV):

    def __init__(self,i, c, r = '4k'):
        super().__init__(i, c, r)
        #super()는 상위 클래스에 받은 i,c,r을 다 올려줌

    def setSmartTV(self,s):
        self.smartTV = s

    def setaiTV(self,s):
        self.aiTV = s