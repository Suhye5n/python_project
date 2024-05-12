import rankmod as rm
import random

midStuScores = random.sample(range(50, 101),20)
finStuScores = random.sample(range(50, 101),20)

rd = rm.RankDeviation(midStuScores, finStuScores)
rd.setMidRank()
print(f'midStuScores: {midStuScores}')
print(f'mid_rank: {rd.getMidRank()}')

rd.setFinRank()
print(f'finStuScores: {finStuScores}')
print(f'fin_rank: {rd.getFinRank()}')

rd.printRankDeviation()