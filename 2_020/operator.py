print('{} and {} : {}'.format(True, True, (True and True)))
print('{} and {} : {}'.format(False, True, (False and True)))
print('{} and {} : {}'.format(True, False, (True and False)))
print('{} and {} : {}'.format(False, False, (False and False)))

print('{} or {} : {}'.format(True, True, (True or True)))
print('{} or {} : {}'.format(False, True, (False or True)))
print('{} or {} : {}'.format(True, False, (True or False)))
print('{} or {} : {}'.format(False, False, (False or False)))

print('not {} : {}'.format(True, (not True)))
print('not {} : {}'.format(False, (not False)))