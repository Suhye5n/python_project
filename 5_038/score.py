uri = '/Users/osuhyeon/Desktop/2024/pythonEx/pythonTxt/'

# scoreDic = {'kor': 85, 'eng': 90,'mat': 92, 'sci': 79, 'his': 82}
# for key in scoreDic.keys():
#     with open(uri + 'scoreDic.txt', 'a') as f:
#         f.write(key + '\t:' + str(scoreDic[key]) + '\n')

scoreDic = {'kor': 85, 'eng': 90,'mat': 92, 'sci': 79, 'his': 82}
scoreList = [56,74,22,126,78]
with open(uri + 'score.txt', 'a') as f:
    print(scoreList, file = f)