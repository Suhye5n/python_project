students = ('김성예', '신경도', '최승철', '황동석')

for i in range(len(students)):
    if i % 2 == 0:
        print('인덱스 짝수: students[{}] : {}'.format(i, students[i]))
    else:
        print('인덱스 홀수: students[{}] : {}'.format(i, students[i]))