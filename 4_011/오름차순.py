numbers = [1,3,6,11,45,54,62,74,85]

userInput = int(input('숫자 입력: '))

insertIdx = 0

for idx, number in enumerate(numbers):
    if userInput < number and insertIdx == 0:
        #여기서 insertIdx==0이라는 조건을 안넣으면 1을 넣었을때도 85까지 인덱스가 돈다
        #한번 넣을 인덱스를 찾으면 이후 계산으로 넘어가지 않게 해줘야 한다
        insertIdx = idx


numbers.insert(insertIdx, userInput)
print('numbers : {}'.format(numbers))