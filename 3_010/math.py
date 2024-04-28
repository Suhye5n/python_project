dNum = 30

print('2진수: {}'.format(bin(dNum)))
print('8진수: {}'.format(oct(dNum)))
print('16진수: {}'.format(hex(dNum)))

print('2진수: {}'.format(dNum, 'b'))
print('8진수: {}'.format(dNum, 'o'))
print('16진수: {}'.format(dNum, 'x'))


print('{0:#b} {0:#o} {0:#x}'.format(dNum))

print('2진수: {}'.format(int('11110', 2)))
print('8진수: {}'.format('0o36', 8))
print('16진수: {}'.format('0x1e', 16))