from test import function, loop
import time

start = time.time()
print(loop(2000))
end = time.time()
print(end - start)


def loop2(num: int):
    a = 0
    for j in range(num):
        for k in range(num):
            a = a + 1
    return a

start = time.time()
print(loop2(2000))
end = time.time()
print(end - start)


print(function(4, 5))
