a = []

for i in range(10):
    def test():
        return 1
    a.append(test)

for i in a:
    print(id(i))