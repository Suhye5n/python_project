for i in range(1, 10):
    for j in range(2, 10):
        result = j * i
        print('{} * {} = {}'.format(j, i, result), end='\t')
    print()