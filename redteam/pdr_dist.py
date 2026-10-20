import csv, sys, collections, statistics as st
sys.stdout.reconfigure(encoding="utf-8")
for path in sys.argv[1:]:
    rows=list(csv.DictReader(open(path)))
    print("==",path.split("darwinV2/")[-1], len(rows))
    by=collections.defaultdict(list)
    for r in rows: by[(r["agent"],r.get("size",""))].append(r)
    for k,v in sorted(by.items()):
        p=[float(r["mean_pdr_seen"]) for r in v if r["mean_pdr_seen"] not in ("","nan")]
        s=[float(r["steps_to_safe"]) for r in v if r["steps_to_safe"] not in ("","nan")]
        succ=sum(r["success"]=="True" for r in v)
        c=collections.Counter(round(x,3) for x in p)
        top=c.most_common(4)
        exact0=sum(1 for x in p if x==0.0); exact05=sum(1 for x in p if abs(x-0.5)<1e-12); exact1=sum(1 for x in p if x==1.0)
        sc=collections.Counter(int(x) for x in s)
        print(f"{k[0]:18s} n={len(v)} succ={succ} steps={dict(sorted(sc.items()))} meanPDR={st.mean(p):.4f} medPDR={st.median(p):.4f} ==0:{exact0} ==0.5:{exact05} ==1:{exact1} top={top}")
