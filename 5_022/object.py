class NormalCar:

    def drive(self):
        print('[NormalCar drive() called!!' )

    def back(self):
        print('[NormalCar back() called!!')

class TurboCar(NormalCar):

    def turbo(self):
        print('[TurboCar turbo() called!!')

myTurboCar = TurboCar

myTurboCar.turbo()
myTurboCar.back()
myTurboCar.drive()