def fun1():
    print('fun1 호출!')
    fun2()
    print('fun2 호출 후에 실행!')

def fun2():
    print('fun2 호출!')
    fun3()

def fun3():
    print('fun3 호출!')

fun1()