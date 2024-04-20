cha1 = 'A' #65
cha2 = 'S' #83

print('\'{}\' > \'{}\' : {}'.format(cha1, cha2, (cha1 > cha2)))
print('\'{}\' >= \'{}\' : {}'.format(cha1, cha2, (cha1 >= cha2)))
print('\'{}\' < \'{}\' : {}'.format(cha1, cha2, (cha1 < cha2)))
print('\'{}\' <= \'{}\' : {}'.format(cha1, cha2, (cha1 <= cha2)))

print('\'A\' -> {}'.format(ord('A')))
print('\'S\' -> {}'.format(ord('S')))

print('\'a\' -> {}'.format(ord('a')))
print('\'s\' -> {}'.format(ord('s')))

print('65 -> {}'.format(chr(65)))
print('83 -> {}'.format(chr(83)))

str1 = 'Hello'
str2 = 'hello'

print('{} == {} : {}'.format(str1, str2, (str1 == str2)))
print('{} != {} : {}'.format(str1, str2, (str1 != str2)))