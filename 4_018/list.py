import random

sampleList = random.sample(range(1, 11), 10)

selectIdx = int(input('숫자 7의 위치 입력: '))
searchIdx = sampleList.index(7)

if searchIdx == selectIdx:
    print('빙고!!')

else:
    print('ㅜㅜ')

print('sampleList: {}'.format(sampleList))
print('sampleIdx: {}'.format(searchIdx))