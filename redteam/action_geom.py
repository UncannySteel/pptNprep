# Re-implements src/sim/topology.py grid + corner safe zones, and env.py ID-sorted action indexing.
import math, sys, collections, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
SP,RNG,K=400.0,1500.0,8
def build(n):
    pos={f"N{r*n+c:03d}":(c*SP,r*SP) for r in range(n) for c in range(n)}
    nb={a:sorted(b for b in pos if b!=a and math.dist(pos[a],pos[b])<=RNG) for a in pos}
    return pos,nb
def corners(pos,which):
    mx=max(p[0] for p in pos.values()); my=max(p[1] for p in pos.values())
    cs=[(0,0),(mx,0),(0,my),(mx,my)]
    return [min(pos,key=lambda q:math.dist(pos[q],cs[i])) for i in which]
def bfs(nbrs,src,goals):
    d={src:0};q=collections.deque([src])
    while q:
        u=q.popleft()
        if u in goals: return d[u]
        for v in nbrs[u]:
            if v not in d: d[v]=d[u]+1;q.append(v)
    return None
for n in (10,15):
    pos,nb=build(n)
    for label,which in (("paper (corners[:2] = top-left, top-right)",(0,1)),("hypothetical bottom corners",(2,3))):
        gz=set(corners(pos,which))
        trunc={a:nb[a][:K] for a in nb}
        full=[];tr=[];unreach=0;closer=[];upmoves=[]
        for s in pos:
            if s in gz: continue
            f=bfs(nb,s,gz); t=bfs(trunc,s,gz)
            full.append(f)
            if t is None: unreach+=1
            else: tr.append(t)
            dg=lambda q:min(math.dist(pos[q],pos[g]) for g in gz)
            closer.append(sum(dg(v)<dg(s) for v in trunc[s])/len(trunc[s]))
            upmoves.append(sum(pos[v][1]<pos[s][1] for v in trunc[s])/len(trunc[s]))
        print(f"{n}x{n} {label}: gateways={sorted(gz)}")
        print(f"   optimal hops (full nbr set): mean {st.mean(full):.2f} max {max(full)}")
        print(f"   optimal hops using only 8 lowest-ID slots: mean {(st.mean(tr) if tr else float("nan")):.2f} max {(max(tr) if tr else None)}  unreachable starts {unreach}/{len(full)}")
        print(f"   share of the 8 slots that reduce distance to nearest gateway: mean {st.mean(closer):.2f}")
        print(f"   share of the 8 slots that move toward row 0 (y decreases): mean {st.mean(upmoves):.2f}")
    s="N055"; print("   example: interior node",s,"8 slots ->",[ (v, (int(pos[v][1]//SP)-int(pos[s][1]//SP), int(pos[v][0]//SP)-int(pos[s][0]//SP))) for v in nb[s][:K] ] if n==10 else "")
# degree check
pos,nb=build(10); print("10x10 mean degree",round(st.mean(len(v) for v in nb.values()),2),"max",max(len(v) for v in nb.values()))
