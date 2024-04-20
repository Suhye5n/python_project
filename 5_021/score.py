import copy
scores = [9, 8, 4, 7, 6, 10]
scoresCopy = []

for s in scores:
    scoresCopy.append(s)
print(f'id(scores): {id(scores)}')
print(f'id(scoresCopy): {id(scoresCopy)}')