playerScore = (9.5, 8.9, 9.2, 9.8, 8.8, 9.0)
print('playerScore: {}'.format(playerScore))
print('playerScore type: {}'.format(type(playerScore)))

playerScore = list(playerScore)
print('playerScore type: {}'.format(type(playerScore)))

playerScore.sort()
print('playerScore type: {}'.format(playerScore))

playerScore.pop(0)
playerScore.pop(len(playerScore) - 1)

print('playerScore: {}'.format(playerScore))

playerScore = tuple(playerScore)

print('playerScore: {}'.format(playerScore))

sum = 0
avg = 0
for score in playerScore:
    sum += score

avg = sum / len(playerScore)

print('총점: %.2f' %sum)
print('평점: %.2f' %avg)