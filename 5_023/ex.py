class P_Class:

    def __init__(self, pNum1, pNum2):
        print('[P_class] __init__() called')
        self.pNum1 = pNum1
        self.pNum2 = pNum2

class C_Class(P_Class):

    def __init__(self, cNum1, cNum2):
        print('[C_class] __init__() called')

        super().__init__(cNum1, cNum2)
        self.cNum1 = cNum1
        self.cNum2 = cNum2

cls = C_Class(10, 20)
