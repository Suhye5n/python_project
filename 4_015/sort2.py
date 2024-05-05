playerScore = [9.5, 8.9, 9.2, 9.8, 8.8, 9.0]
print('playerScore: {}'.format(playerScore))

playerScore.sort()
print('playerScore: {}'.format(playerScore))

playerScore.pop(0)
playerScore.pop(len(playerScore)-1)
print('playerScore: {}'.format(playerScore))

sum = 0
avg = 0
for score in playerScore:
    sum += score

avg = sum / len(playerScore)

print('sum: %.2f' % sum)
print('avg: %.2f' % avg)