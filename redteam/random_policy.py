# Trivial policies on the same grid/action encoding (all nodes alive, no failures).
import math, sys, random, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
SP,RNG,K=400.0,1500.0,8
def build(n):
    pos={f"N{r*n+c:03d}":(c*SP,r*SP) for r in range(n) for c in range(n)}
    nb={a:sorted(b for b in pos if b!=a and math.dist(pos[a],pos[b])<=RNG) for a in pos}
    return pos,nb
for n in (10,15):
    pos,nb=build(n); gz={f"N{0:03d}",f"N{n-1:03d}"}
    starts=[s for s in pos if s not in gz]
    rnd=random.Random(0)
    def run(policy, cap=200):
        out=[]
        for _ in range(20000):
            s=rnd.choice(starts); k=0
            while s not in gz and k<cap:
                s=nb[s][policy(s)]; k+=1
            out.append(k)
        return out
    uni=run(lambda s: rnd.randrange(K))
    a0=run(lambda s: 0)
    def greedy(s):
        slots=nb[s][:K]
        return min(range(len(slots)), key=lambda i:min(math.dist(pos[slots[i]],pos[g]) for g in gz))
    gr=run(greedy)
    q=lambda v:(st.median(v), st.quantiles(v,n=4)[0], st.quantiles(v,n=4)[2])
    print(f"{n}x{n}: uniform-random over 8 slots: mean {st.mean(uni):.2f} median/Q1/Q3 {q(uni)} capped {sum(x>=200 for x in uni)}")
    print(f"{n}x{n}: always action 0:            mean {st.mean(a0):.2f} median/Q1/Q3 {q(a0)} capped(200) {sum(x>=200 for x in a0)}")
    print(f"{n}x{n}: greedy-geographic on 8 slots: mean {st.mean(gr):.2f} median/Q1/Q3 {q(gr)}")
