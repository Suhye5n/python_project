class Robot:

    def __init__(self, c, h, w):
        self.color = c
        self.height = h
        self.weight = w

    def fire(self):
        print('미사일 발사!!')

    def printselfRobotInfo(self):
        print(f'self.color: {self.color}')
        print(f'self.height: {self.height}')
        print(f'self.weight: {self.weight}')


class NewRobot(Robot):
    def __init__(self, c, h, w):
        super().__init__(c, h, w)

    def fire(self):
        print('레이저 발사')

myRobot = NewRobot('red', 200, 300)
myRobot.printselfRobotInfo()
myRobot.fire()