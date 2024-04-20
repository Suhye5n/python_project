class Car:

    def __init__(self, col, len):
        self.color = col
        self.length = len

    def doStop(self):
        print('stop')

    def doStart(self):
        print('start')

    def printCarInfo(self):
        print(self.color)
        print(self.length)


car1 = Car('red',200)

car1.printCarInfo()