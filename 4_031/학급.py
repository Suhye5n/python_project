studentsCnts = (1, 18),(2, 19),(3, 23),(4, 21),(5, 20), (6, 22), (7, 17)

minClassNo = 0; maxClassNo = 0
minCnt = 0; maxCnt = 0

n = 0
while n < len(studentsCnts):

    if minCnt == 0 or minCnt > studentsCnts[n][1]:
        minClassNo = studentsCnts[n][0]
        minCnt = studentsCnts[n][1]

    if maxCnt < studentsCnts[n][1]:
        maxClassNo = studentsCnts[n][0]
        maxCnt = studentsCnts[n][1]

    n += 1

print('학생 수가 가장 적은 학급(학생수): {}학급 ({}명)'.format(minClassNo, minCnt))
print('학생 수가 가장 많은 학급(학생수): {}학급 ({}명)'.format(maxClassNo, maxCnt))