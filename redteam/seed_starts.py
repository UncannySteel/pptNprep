# Reproduces DisasterEvacEnv.reset() start-node choice (gymnasium np_random == default_rng(seed),
# first draw integers(0, len(candidates))) for eval seeds 0..99, then scores trivial policies
# on those exact starts. All nodes alive (failures ignored: ~1% chance per path node per episode).
import math, sys, collections, statistics as st
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
SP_,RNG,K=400.0,1500.0,8
def build(n):
    pos={f"N{r*n+c:03d}":(c*SP_,r*SP_) for r in range(n) for c in range(n)}
    nb={a:sorted(b for b in pos if b!=a and math.dist(pos[a],pos[b])<=RNG) for a in pos}
    return pos,nb
def bfs(nbrs,src,goals):
    d={src:0};q=collections.deque([src])
    while q:
        u=q.popleft()
        if u in goals: return d[u]
        for v in nbrs[u]:
            if v not in d: d[v]=d[u]+1;q.append(v)
def walk(nb,s,gz,pol,cap=200):
    k=0
    while s not in gz and k<cap: s=nb[s][pol(s)]; k+=1
    return k
def summ(v):
    q=np.percentile(v,[25,50,75]); return f"median {q[1]:g} [{q[0]:g}, {q[2]:g}] mean {np.mean(v):.2f}"
for n in (10,15):
    pos,nb=build(n); gz={f"N000",f"N{n-1:03d}"}
    cands=sorted(x for x in pos if x not in gz)
    starts=[cands[int(np.random.default_rng(s).integers(0,len(cands)))] for s in range(100)]
    opt=[bfs(nb,s,gz) for s in starts]
    a0=[walk(nb,s,gz,lambda u:0) for s in starts]
    print(f"{n}x{n} optimal hops on eval starts: {dict(sorted(collections.Counter(opt).items()))}  {summ(opt)}")
    print(f"{n}x{n} always-action-0 on eval starts: {dict(sorted(collections.Counter(a0).items()))}  {summ(a0)}")
