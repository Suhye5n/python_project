from abc import ABCMeta
from abc import abstractmethod

class AirPlane(metaclass = ABCMeta):

    @abstractmethod
    def flight(self):
        pass

    def forward(self):
        print('전진')

    def backward(self):
        print('후진')

class Airliner(AirPlane) :

    def __init__(self,c):
        self.color = c

    def flight(self):
        print('시속 204km로 달리기')

class fightPlane(AirPlane):

    def __init__(self, c):
        self.color = c

    def flight(self):
        print('겁나게 빨리 달려버리기')

al = Airliner('red')
al.flight()

fl = fightPlane('blue')
fl.flight()