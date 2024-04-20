def printScore(kor, eng, math):
    sum = kor + eng + math
    avg = sum/3
    print(f'총점: {sum}')
    print(f'총점: {avg}')

korScore = int(input('국어 점수 입력:'))
engScore = int(input('영어 점수 입력:'))
mathScore = int(input('수학 점수 입력:'))

printScore(korScore, engScore, mathScore)