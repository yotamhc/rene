import math
import random

W = 16
H_max = 16

def brgc(value):
    return value ^ (value >> 1)

def print_binary(value):
    print bin(value)[2:].zfill(32)

def get_ternary((value, mask)):
    b = bin(value)[2:].zfill(32)
    m = bin(mask)[2:].zfill(32)
    res = ''
    for i in range(32):
        if m[i] == '1':
            res = res + '*'
        else:
            res = res + b[i]
    return res
        
def print_ternary((value, mask)):
    print get_ternary((value, mask))
    
def encodeValue(i):
    gray = brgc(i)
    word = gray >> int(math.log(H_max, 2) - 1)
    for x in range(H_max):
        if x != 0 and x != H_max/2:
            b = 1-int(math.floor((i - x) / float(H_max))) % 2
            word = (word << 1) | b
    return word

def encodeRange(s, t):
    gamma = []
    if (t - s + 1) < H_max:
        r1 = (s, s+H_max-1)
        r2 = (t-H_max+1, t)
        gamma.append(r1)
        gamma.append(r2)
    else:
        gamma.append((s, t))
        
    r_value = 0
    r_mask = (-1) & 0x0FFFF
    count = 0
    for (x,y) in gamma:
        mask = 0
        for i in range(x+1, y+1):
            mask = mask | (brgc(i) ^ brgc(i-1))
        word = brgc(s) >> int(math.log(H_max, 2) - 1)
        mask = mask >> int(math.log(H_max, 2) - 1)
        for i in range(H_max):
            if i != 0 and i != H_max/2:
                if x % H_max != i:
                    mask = (mask << 1) | 1
                    word = word << 1
                else:
                    mask = mask << 1
                    b = 1-int(math.floor((i - x) / float(H_max))) % 2
                    word = (word << 1) | b
        if count > 0:
            (r_value, r_mask) = conj((r_value, r_mask), (word, mask))
        else:
            (r_value, r_mask) = (word, mask)
        count = count + 1

    return (r_value, r_mask)

def conj_bit(a, b):
    if a == b:
        return a
    if a == '*':
        return b
    if b == '*':
        return a
    else: 
        return None

def conj(r1, r2):
    t1 = get_ternary(r1)
    t2 = get_ternary(r2)
    value = ['0'] * 32
    mask = ['0'] * 32
    
    for i in range(len(t1)):
        res = conj_bit(t1[i], t2[i])
        if res == None:
            return None
        if res == '*':
            mask[i] = '1'
        else:
            value[i] = res
            
    return (int(''.join(value), 2), int(''.join(mask), 2))

def ternaryMatch((v1, m1), (v2, m2)):
    return (v1 & ~m1 & ~m2) == (v2 & ~m1 & ~m2)

def test():
    # Creates random ranges and tests points in each range 
    
    for i in range(10000):
        s = random.randint(0, 2**W)
        len = random.randint(2, H_max)
        e = s + len - 1
        (vr, mr) = encodeRange(s, e)
        
        for j in range(100):
            p = random.randint(0, 2**W)
            vp = encodeValue(p)
            
            if (p >= s and p <= e and not ternaryMatch((vr, mr), (vp, 0))) or ((p < s or p > e) and ternaryMatch((vr, mr), (vp, 0))):
                print "ERROR: TEST FAILED FOR RANGE [%d, %d] AND POINT %d:" % (s, e, p)
                print "Range encoding: ",
                print_ternary((vr, mr))
                print "Point encoding: ",
                print_binary(vp)
                return False
            
    print "TEST SUCCEEDED!"
    return True
    
if __name__ == "__main__":
    test()

