students =('홍길동', '박찬호', '이용규', '박승철', '김지은')
print('students : {}'.format(students))

students = list(students)
students.sort(reverse = True)
students = tuple(students)

print('students : {}'.format(students))

sortedStudents = sorted(students)
print(sortedStudents)