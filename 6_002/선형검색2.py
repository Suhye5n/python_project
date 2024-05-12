nums = [4, 7, 10, 2, 4, 7, 0, 2, 7, 3, 9]
print(f'nums:{nums}')
print(f'nums length: {len(nums)}')

def searchDatas(tempNums):
    searchData = int(input('input search number: '))
    searchResultIdxs = []
    tempNums.append(searchData)
    # 여기서 사용자가 입력한 데이터를 맨 뒤에 붙이는 이유는 뒤에 반복문 나올때 n+=1이 계속 붙기 때문에
    # 맨 처음 시작할때 불필요한 searchResultIdx = -1 를 쓰지 않아도 됨

    n = 0
    while True:

      if tempNums[n] == searchData:
          if n != len(tempNums) -1:
              searchResultIdxs.append(n)
          else:
              break

      n += 1
    print(f'searchResultIdx: {searchResultIdxs}')
    print(f'searchResultCnts: {len(searchResultIdxs)}')

searchDatas(nums)

