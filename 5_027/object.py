class TriangleArea:

    def __init__(self, w, h):
        self.width = w
        self.height = h

    def printTriangleAreaInfo(self):
        print(f'self.width: {self.width}')
        print(f'self.height: {self.height}')

    def getArea(self):
        return self.width * self.height / 2

class NewTriangleArea(TriangleArea):

    def __init__(self, w, h):
        super().__init__(w, h)

    def getArea(self):
        return str(super().getArea()) + 'cm^2'

Triangle = NewTriangleArea(7, 3)
Triangle.printTriangleAreaInfo()
ta = Triangle.getArea()
print(ta)