myNumbers = (1, 3, 5, 6, 7)
friendNumbers = (2, 3, 5, 8, 10)

print('myNumbers: {}'.format(myNumbers))
print('friendNumbers: {}'.format(friendNumbers))

for number in friendNumbers:
    if number not in myNumbers:
        myNumbers = myNumbers + (number, )

print('myNumbers : {}'.format(myNumbers))