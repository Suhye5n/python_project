class Robot:

    def __init__(self, color, height, weight):
        self.color = color
        self.height = height
        self.weight = weight

    def printRobotInfo(self):
        print(f'color: {self.color}')
        print(f'height: {self.height}')
        print(f'weight: {self.weight}')

rb1 = Robot('red', 200, 80)
rb2 = Robot('blue', 300, 120)
rb3 = rb1 #얕은 복사

rb1.color = 'gray'
rb1.weight = 56

rb1 = Robot('red', 200, 80)
rb2 = Robot('blue', 300, 120)