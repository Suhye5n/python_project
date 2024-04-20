cnt = 0

for i in range(100):
    if i % 7 != 0:
        continue

    print('{}는 7의 배수입니다.'.format(i))
    cnt += 1

else:
    print('{}개'.format(cnt))