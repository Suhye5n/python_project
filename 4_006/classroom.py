students = [[1,18],
            [2,19],
            [3,23],
            [4,21],
            [5,20],
            [6,22],
            [7,17]]

minClass = 0; minStudent = 0
maxClass = 0; maxStudent = 0

for classroom, studentCnt in students:
    if classroom == 1:
        minStudent = studentCnt

    elif studentCnt <= minStudent:
        minClass = classroom
        minStudent = studentCnt

    elif studentCnt >= maxStudent:
        maxClass = classroom
        maxStudent = studentCnt


print('학생 수가 가장 적은 학급(학생수): {}학급({}명)'.format(minClass,minStudent))
print('학생 수가 가장 많은 학급(학생수): {}학급({}명)'.format(maxClass,maxStudent))