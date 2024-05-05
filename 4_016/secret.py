secret = '27156231'

secretList = []
solvedList = ''

for cha in secret:
    secretList.append(int(cha))

print('secretList : {}'.format(secretList))

secretList.reverse()

val = secretList[0] * secretList[1]
secretList.insert(2,val)

val = secretList[3] * secretList[4]
secretList.insert(5,val)

val = secretList[6] * secretList[7]
secretList.insert(8,val)

val = secretList[9] * secretList[10]
secretList.insert(11,val)

for cha in secretList:
    solvedList = solvedList + str(cha)

print(solvedList)