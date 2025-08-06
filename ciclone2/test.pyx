
def loop(int num):
    cdef:
        int j, k
        int a = 0
    for j in range(num):
        for k in range(num):
            a = a + 1
    return a

def function(a: int, b: int) -> str:
    return str(a + b)

print(function(2, 4))
