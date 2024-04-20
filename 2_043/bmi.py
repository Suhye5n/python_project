weight = input('체중 입력(g): ')
height = input('신장 입력(cm): ')

if weight.isdigit ():
    weight = int(weight) / 10
if height.isdigit ():
    height = int(height) / 100

print('체중: {}kg'.format(weight))
print('신장: {}m'.format(height))

bmi = weight / (weight * height)
print('%.2f'%bmi)
