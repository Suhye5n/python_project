class Calculator:

    def __init__(self):
        self.number1 = 0
        self.number2 = 0
        self.result = 0

    def add(self):
        self.result = self.number1 + self.number2
        return self.result

    def sub(self):
        self.result = self.number1 - self.number2
        return self.result

    def mul(self):
        self.result = self.number1 * self.number2
        return self.result

    def div(self):
        self.result = self.number1 / self.number2
        return self.result

calculator = Calculator()
#글로벌 변수에 클래스를 할당
calculator.number1 = 10
calculator.number2 = 20

print(f'calculator.add(): {calculator.add()}')
print(f'calculator.sub(): {calculator.sub()}')
print(f'calculator.mul(): {calculator.mul()}')
print(f'calculator.div(): {calculator.div()}')
