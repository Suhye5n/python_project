class TemCls:

    def __init__(self, n, s):
        self.number = n
        self.str = s

    def printClsInfo(self):
        print(f'self.number : {self.number}')
        print(f'self.str : {self.str}')

#얕은 복사
# tc1 = TemCls(10, 'Hello')
# tc2 = tc1
#
# tc1.printClsInfo()
# tc2.printClsInfo()
#
# tc2.number = 3.14
# tc2.str = 'Bye'
#
# tc1.printClsInfo()
# tc2.printClsInfo()

#깊은 복사

import copy

tc1 = TemCls(10, 'Hello')
tc2 = copy.copy(tc1)

tc2.number = 3.14
tc2.str = 'Bye'

tc1.printClsInfo()
tc2.printClsInfo()