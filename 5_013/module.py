import unitConversion as uc

inputNumber = int(input('길이(cm) 입력: '))
returnValue = uc.cmToMm(inputNumber)
print(f'returnValue: {returnValue}mm')