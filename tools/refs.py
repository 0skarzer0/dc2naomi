import struct, sys
b=open('files/1ST_READ.BIN','rb').read(); base=0x8c010000
def refs(lit):
    out=[]
    for i in range(0,len(b)-1,2):
        op=struct.unpack_from('<H',b,i)[0]
        pc=base+i
        if op>>12==0xD:
            t=(pc&~3)+4+(op&0xff)*4
            if t==lit: out.append(pc)
        elif op>>12==0x9:
            t=pc+4+(op&0xff)*2
            if t==lit: out.append(pc)
    return out
for a in sys.argv[1:]:
    print(a,[hex(x) for x in refs(int(a,16))])
