class MidExam:

    def __init__(self, s1, s2, s3):
        print('[MidExam]__init()')
        self.mid_kor = s1
        self.mid_eng = s2
        self.mid_math = s3

    def printScores(self):
        print(f'mid_kor: {self.mid_kor}')
        print(f'mid_eng: {self.mid_eng}')
        print(f'mid_math: {self.mid_math}')

class FinExam(MidExam):

    def __init__(self, s1, s2, s3, s4, s5, s6):
        print('[finExam]__init()')

        super().__init__(s1, s2, s3)
        self.fin_kor = s4
        self.fin_eng = s5
        self.fin_math = s6

    def printScores(self):
        super().printScores() #중간고사 점수 출력
        print(f'fin_kor: {self.mid_kor}')
        print(f'fin_eng: {self.mid_eng}')
        print(f'fin_math: {self.mid_math}')

    def getTotalScore(self):
        total = self.mid_kor + self.mid_eng + self.mid_math
        total += self.fin_kor + self.fin_eng + self.fin_math

        return total

    def getAverageScore(self):
        return self.getTotalScore() / 6

exam = FinExam(85, 23, 46, 57, 89, 86)
exam.printScores()

print(f'Total: {exam.getTotalScore()}')
print(f'Average: {exam.getAverageScore()}')