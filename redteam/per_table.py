# Reimplements src/comm/phy.py formulas (no import from the code dir).
import math, sys
sys.stdout.reconfigure(encoding="utf-8")
TX=20.0; NF=6.0; NOISE=-174+10*math.log10(125e3)+NF; THR=-20.0; k=1.5
def pl(d,n): return 31.2+10*n*math.log10(max(d,1))
def per(snr): return 1/(1+math.exp(k*(snr-THR)))
pres={"intact":(2.7,7.0),"moderate":(3.0,9.0),"heavy":(3.8,11.0),"severe":(4.2,12.5),"extreme":(4.5,14.0)}
ds=sorted({round(400*math.hypot(a,b),1) for a in range(4) for b in range(4) if 0<400*math.hypot(a,b)<=1500})
print("noise floor",round(NOISE,2))
print("dist_m  "+"  ".join(f"{p:>9}" for p in pres))
import random
rng=random.Random(1)
for d in ds:
    row=[]
    for p,(n,s) in pres.items():
        snr=TX-pl(d,n)-NOISE
        row.append(f"{1-per(snr):9.4f}")
    print(f"{d:7.1f} "+"  ".join(row))
print("\nwith shadowing (Fig.2 model), MC mean PDR")
for d in ds:
    row=[]
    for p,(n,s) in pres.items():
        snr=TX-pl(d,n)-NOISE
        N=20000; acc=0
        for _ in range(N): acc+=1-per(snr+rng.gauss(0,s))
        row.append(f"{acc/N:9.4f}")
    print(f"{d:7.1f} "+"  ".join(row))
print("\nRSSI margin between 400 m and 565.7 m transmitters (dB) = 10 n log10(sqrt2)")
for p,(n,s) in pres.items(): print(p, round(10*n*math.log10(math.sqrt(2)),2), ">=6 capture" if 10*n*math.log10(math.sqrt(2))>=6 else "<6 collide")
# duty cycle
def toa(pl_b,sf=12,bw=125e3,cr=1,pre=8):
    ts=2**sf/bw*1e3; de=1; ih=0
    num=8*pl_b-4*sf+28+16-20*ih; den=4*(sf-2*de)
    return (pre+4.25)*ts+(8+max(math.ceil(num/den)*(cr+4),0))*ts
for b in (4,20,34,38,51,76):
    t=toa(b)/1000; print(f"payload {b:3d} B ToA {t:.3f} s  duty@30s {100*t/30:.2f}%")
