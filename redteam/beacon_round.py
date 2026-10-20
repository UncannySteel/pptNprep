# Re-implements TimeSteppedMeshStateProvider._contention_mask for one beacon round
# (every alive node transmits in the same propagation round, as _inject_beacons does at t = 30, 60, ...).
import math, sys
sys.stdout.reconfigure(encoding="utf-8")
SP_,RNG=400.0,1500.0
def pl(d,n): return 31.2+10*n*math.log10(max(d,1))
pres={"intact":2.7,"moderate":3.0,"heavy":3.8,"severe":4.2,"extreme":4.5}
for size in (10,15):
    pos={f"N{r*size+c:03d}":(c*SP_,r*SP_) for r in range(size) for c in range(size)}
    nb={a:[b for b in pos if b!=a and math.dist(pos[a],pos[b])<=RNG] for a in pos}
    for p,n in pres.items():
        survived=0; attempts=0
        for rx in pos:
            txs=nb[rx]  # all neighbours transmit a beacon this round
            attempts+=len(txs)
            rs=sorted((20-pl(math.dist(pos[t],pos[rx]),n) for t in txs),reverse=True)
            if len(rs)<2 or rs[0]-rs[1]>=6.0: survived+=1  # only the single strongest tx survives
        print(f"{size}x{size} {p:8s}: beacon receptions surviving contention {survived}/{attempts} ({100*survived/attempts:.2f}%)")
