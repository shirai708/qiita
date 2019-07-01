def func1():
    a = 10

    def func2():
        nonlocal a
        a = 20
    func2()
    print(a)


func1()
