class RankDeviation:

    def __init__(self, mss, fss):
        self.midScores = mss
        self.finScores = fss
        self.midRanks = [0 for i in range(len(mss))]
        self.finRanks = [0 for i in range(len(fss))]
        self.rankDeviation = [0 for i in range(len(mss))]

    def setRank(self, score, rank):
        for idx, score1 in enumerate(score):
            for score2 in score:
                if score1 < score2:
                    rank[idx] += 1

    def setMidRank(self):
        self.setRank(self.midScores, self.midRanks)

    def getMidRank(self):
        return self.midRanks
        #순위 잘 정해졌는지 확인용

    def setFinRank(self):
        self.setRank(self.finScores, self.finRanks)

    def getFinRank(self):
        return self.finRanks
        # 순위 잘 정해졌는지 확인용

    def printRankDeviation(self):
        for idx, mRank in enumerate(self.midRanks):
            deviation = mRank - self.finRanks[idx]

            if deviation > 0:
                deviation = '높아유 ' + str(abs(deviation))

            elif deviation < 0:
                deviation = '낮아유 ' + str(abs(deviation))

            else:
                deviation = '='

            print(f'mid_rank: {mRank} \t fin_rank: {self.finRanks[idx]} \t Deviation: {deviation}')

