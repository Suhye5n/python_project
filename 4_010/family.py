myFamilyAge = [['아빠',40],['엄마',38],['나',9]]
print(myFamilyAge)

myFamilyAge.append(['동생',1])
print(myFamilyAge)

for name, age in myFamilyAge:
    print('{} : {}'.format(name, age))