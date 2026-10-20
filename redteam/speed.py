import csv,sys,statistics as st,collections
sys.stdout.reconfigure(encoding="utf-8")
for p in sys.argv[1:]:
    d=collections.defaultdict(list)
    for r in csv.DictReader(open(p)):
        if r["mean_wall_time_s"]=="TIMEOUT": continue
        d[(r["backend"],int(r["size"]))].append(float(r["mean_wall_time_s"]))
    print("==",p.split("/")[-1])
    for s in sorted({k[1] for k in d}):
        a=d.get(("simpy",s)); b=d.get(("timestep",s))
        if a and b: print(f"{s}x{s}: simpy {st.mean(a):.4f}s  timestep {st.mean(b):.4f}s  speedup {st.mean(a)/st.mean(b):.1f}x  (median-based {st.median(a)/st.median(b):.1f}x)")
        else: print(f"{s}x{s}: simpy {'TIMEOUT' if not a else st.mean(a)} timestep {st.mean(b) if b else None}")
