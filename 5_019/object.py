class NewGenerationPC:

    def __init__(self, name, cpu, memory, ssd):
        self.name = name
        self.cpu = cpu
        self.memory = memory
        self.ssd = ssd

    def doExcel(self):
        print('EXCEL RUN')

    def doPhotoshop(self):
        print('Photoshop RUN')

    def printPCInfo(self):
        print(f'self.name: {self.name}')
        print(f'self.cpu: {self.cpu}')
        print(f'self.memory: {self.memory}')
        print(f'self.ssd: {self.ssd}')

myPC = NewGenerationPC('myPC','i5','16G', '256G')
myPC.printPCInfo()

yourPC = NewGenerationPC('yourPC','i7','32G', '512G')
yourPC.printPCInfo()

myPC.cpu = 'i9'
myPC.memory = '64G'
myPC.printPCInfo()