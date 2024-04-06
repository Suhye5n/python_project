allStudent = int(input('학급 전체 학생수 : '))
groupStudent = int(input('한 모둠당 학생수: '))
groupCount = allStudent // groupStudent
stuOverCount = allStudent % groupStudent

print('모둠 수: {}'.format(groupCount))
print('남는 학생 수: {}'.format(stuOverCount))

result = divmod(allStudent, groupStudent)
print('모둠 수: {}'.format(result[0]))
print('남는 학생 수: {}'.format(result[1]))