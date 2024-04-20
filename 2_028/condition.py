selectNum = int(input('출퇴근 대상자 인가요?1.Yes \t2.No'))

if selectNum == 1:
    print('교통수단을 입력하세요.')
    trans = int(input('1.도보, 자전거  2.버스,지하철  3.자가용'))

    if trans == 1:
        print('세금 감면 : 5%')
    elif trans == 2:
        print('세금 감면 : 3%')
    elif trans == 3:
        print('추가 세금 : 1%')

elif selectNum == 2:
    print('세금 변동 없습니다.')

else:
    print('잘못 입력했습니다.')