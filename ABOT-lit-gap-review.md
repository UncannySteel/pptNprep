# ABOT literature gap: how it differs from existing systems, checked against the code

*Written 2026-10-15. Source: paper Section II ("Related Work" and "Gap in Literature"), checked against the code in `<CODE>/darwinV2/` (read, not run) and against the red-team notes (`ABOT-red-team.md` §5, §11; `ABOT-red-team-explained.md` P-03, P-04, P-07, P-10, P-11, P-22, P-24, P-25). Code paths are relative to `<CODE>/darwinV2/`.*

## Bottom line

1. **The difference that holds up best concerns PDR.** In prior work, PDR is the *result*: did the messages arrive? In ABOT, a link-quality score is an *input*: it decides which route gets picked. The code supports this.
2. **It cuts both ways.** ABOT never measures what prior work measures. There is no count of SOS messages reaching a rescuer, and no delay.
3. **All three gaps are real answers, but the code supports a narrower version of each than the paper's wording.** Section 2 gives the safe version of each.
4. **Two of the paper's contrasts don't hold.**
   - It faults [7] for not testing "progressive infrastructure failure", but ABOT doesn't test that either.
   - It contrasts ABOT with "failure-triggered recomputation", but ABOT's own planner also recomputes on a trigger. Its trigger just fires earlier: it includes a falling link score, not only a node dying.

---

## 1. Material for your own lit-gap slide

### Existing work, and how ABOT differs

| Existing work | What it shows | What it leaves open (paper's words) | ABOT's difference (safe wording) |
|---|---|---|---|
| Titan [4] | LoRa works for search-and-rescue coordination | Centralised, built around rescue teams | No hub or gateway: every node both sends and relays |
| Gateway-free ESP32 mesh [5] | A self-forming, self-healing LoRa mesh, **with hardware results** | The paper doesn't say | The closest work to ABOT. ABOT adds routing on link quality and a test across damage levels; [5] is ahead on hardware evidence |
| AI-optimised mesh routing [7] | Smarter routing improves delivery, delay and energy | Not built for LoRa's radio limits; not tested as infrastructure fails | ABOT models LoRa's radio limits. **Don't claim the "infrastructure fails" part** (§3.3) |
| Power-aware routing, PARA [8] | Routing by the energy left in downstream nodes improves delivery | Cited for gap 2 | ABOT routes by link quality, not energy. Don't compare on energy (§3.4) |
| IoT disaster systems | Sensors and monitoring help situational awareness | Depend on internet, cloud or a central aggregator | Needs no internet or cloud |
| Meshtastic [12], Project OWL / DuckLink [13], Disaster Radio | LoRa meshes work in the field | No simulator fast enough to train routing agents | A fast simulator with a standard RL interface. ABOT is meant to run as firmware on these same boards, so it complements them rather than competing |

### The three gaps, in safe wording

| Gap (in the work reviewed) | ABOT's answer | What the simulation shows |
|---|---|---|
| 1. LoRa simulators are built for protocol analysis, not for training a routing agent | A fast time-stepped simulator behind a standard RL interface | About 4.7× faster than our own SimPy reference at the 10×10 grid used, and up to 7.3× on a small grid |
| 2. Link-quality routing uses a fixed topology, or recomputes only after a failure | Each node keeps a live link-quality score. The planner avoids weak nodes, and replans when a node ahead dies or its score drops below 0.5 | Routes score about 1.8× higher on link quality (0.267 vs 0.145, over 100 matched episodes). This shows **route choice, not delivery** |
| 3. Adaptive routing is rarely tested across infrastructure damage | Five damage levels, from intact to extreme | The score advantage holds at every level (≈1.5–1.9×). Every planner still reaches a safe zone ~100% of the time, so this is **not a robustness result** |

One line worth adding under the table: *"The planners in these results are given a full view of the network: a best case."*

### Rules for the slide's wording

1. **Scope every gap to "the work we reviewed".** Never say "no one has done this".
   - Why: mesh-routing protocols such as ETX, OLSR-ETX, B.A.T.M.A.N. and Babel already route on continuously updated link quality, mostly on Wi-Fi meshes. The paper cites none of them (red team §11; outside facts, so check them before quoting).
2. **Cite [8] as "PARA [8]" or just "[8]", without an author name.**
   - Why: the paper's text says "Al-Hadhrami et al. [8]", but reference [8] is Olajide (PARA, PLoS ONE 2018).
3. **Don't put [11] on the IoT row.**
   - Why: [11] is Acosta-Garcia et al., a deep-RL paper on LoRa transmission policy, not an IoT situational-awareness paper.
   - It's also a weak citation for gap 1, because [11] itself builds a deep-RL environment for LoRa.

---

## 2. The three gaps, checked against the code

### Gap 1: "no agent interface at RL episode rates" → a vectorised simulator

**What supports it**
- The RL interface exists: `DisasterEvacEnv` is a standard Gymnasium environment (`src/nav/env.py:36`).
- The fast backend draws a whole round of radio-link outcomes in one vectorised pass, instead of one event per transmission (`src/sim/timestep.py:476, 515`).
- The speed-up is real. Recomputed from the committed `results_rev1/scalability.csv` (contention on): 7.2× at 5×5, **4.7× at 10×10**, 4.0× at 15×15.

**What counts against it**
1. **It is timed only against the authors' own SimPy simulator.**
   - Why it matters: it says nothing about ns-3, FLoRa or any other tool.
2. **Part of the speed comes from a simpler model.** The fast backend uses average path loss with no shadowing, i.e. no random signal fading (`timestep.py:157-169`). Every beacon is also sent in the same round, so they all collide (red team §11).
   - Why it matters: the two simulators agree on which nodes are alive (KS p = 0.98) but not on PDR or delivery counts (p < 10⁻³). The paper says this itself in Section IV.
3. **Similar tools exist:** ns3-gym, which pairs with ns-3's LoRaWAN module, plus FLoRa, LoRaSim and Meshtastic's own Meshtasticator (outside facts; check them before quoting).
   - Why it matters: "LoRa simulators lack an RL interface" as a general claim is easy to challenge.

**Verdict: holds, narrowly.** Say "a fast, mesh-specific RL environment". Don't say "the first", and don't say "no simulator offers this".

### Gap 2: "static topology or failure-triggered recomputation, rather than continuously updated PDR" → live link state

This is the PDR gap, and the one to get exactly right.

**What supports it**
- **The static planner** computes its route once at the start and never reacts (`src/train/baselines.py:23-60`). That is the "static topology" side of the contrast.
- **The dynamic planner** gets a fresh network snapshot every step (`src/train/runner.py:93-97`).
  - Its route cost is 1 ÷ link score per hop (`baselines.py:339-342`), so weak nodes look "far".
  - It replans when any of the next three nodes **dies or scores below 0.5** (`baselines.py:312-320`). So it reacts to a falling score before a node fails, which is what Section III promises: "deprioritize a node with falling PDR … before it fails outright".
- **The result:** 0.267 vs 0.145 (1.84×, p = 6.5 × 10⁻⁹, 100 matched episodes; `results_commaware/FINDINGS.md` §2).
  - Supporting check: on the 43 seeds where both planners start on the same route, 0.3098 vs 0.2067 (1.50×, p = 0.0057).

**What counts against it**
1. **ABOT's planner also recomputes on a trigger.** It doesn't recompute continuously: it checks every step, and recomputes only when the trigger fires.
   - Why it matters: the gap contrasts "failure-triggered recomputation" with "continuously updated PDR". The accurate description of ABOT is **"monitored continuously, replanned when a link degrades, before it fails"**. That is a real difference from "only after failure", but it isn't continuous recomputation.
2. **The first route is plain hop count.** The planner's first route is computed from an empty snapshot, so every link weighs the same (`baselines.py:283`; the paper says so in V-C).
   - Why it matters: link quality only affects the route after the first trigger fires.
3. **The "PDR" isn't what Section III describes.** Section III says each receiver works it out from the beacons it hears. In the code it is:
   - a per-node figure: the average over a node's ~30 outgoing links,
   - with each link's success rate taken over its last 50 send attempts, all traffic types,
   - with a link never tried counting as 1.0,
   - recorded on the **sender's** side, from the simulator's own record of what got through (`timestep.py:538-545, 720-733`; the SimPy backend does the same, `src/sim/node.py:458-481`).
   - Why it matters: a real node couldn't know this without acknowledgements, and "never tried = 1.0" lets a node score high just by sending little.
4. **The planners read the whole network from the simulator.** Beacons carry only the sender's ID, and the ROUTE_UPDATE message type is never sent (red team §4.8).
   - Why it matters: the result shows what an all-knowing planner would do, not what the decentralised protocol can do.
5. **The scoring is circular.** The planner chooses routes to maximise the link score, and is then graded on that same score (P-07).
   - Why it matters: a higher score shows the routes changed. It doesn't show that more messages arrive.
6. **This is a known metric.** A cost of 1 ÷ PDR per link is ETX (De Couto et al., MobiCom 2003). Mesh protocols already update it continuously (outside facts; check them before quoting).

**Verdict: holds as "live link-quality scores change which routes get picked".** It doesn't hold as "a new metric", and not as "a delivery gain".

### Gap 3: "rarely benchmarked across infrastructure degradation" → the five-preset sweep

**What supports it**
- The five presets are in the code (`src/config.py:142-148`).
- Every agent was swept at 250 episodes per preset (`results_rev1/damage_severity.csv`; static planners in `results_commaware/commaware_severity_episodes.csv`).
- The Dijkstra link-score ratio by preset is 1.88 / 1.80 / 1.92 / 1.48 / 1.53, from intact to extreme (`FINDINGS.md` §2).

**What counts against it**
1. **Damage can't make a hop fail.** A move succeeds whenever the next node is alive, however weak the link (`env.py:311-313`).
   - Why it matters: success is ~100% at every level by construction, so the sweep can't show robustness.
2. **The static planners take the same number of steps at all five levels**, in 250 of 250 episodes.
   - Why it matters: for them, the sweep changes nothing.
3. **With no shadowing, every in-range link works ≥ 99.96% of the time from intact through heavy.** Only the long links fail, and only at severe and extreme (context §15).
   - Why it matters: at the first three levels the score measures collisions, not damage. That is why the dynamic planner's score drops in one step at severe (≈0.28 → 0.218), not gradually.
4. **The damage levels change the radio, not node failures.** "Infrastructure degradation" here means weaker links, not nodes dying over time (§3.3).

**Verdict: the benchmark exists, but it isn't evidence of robustness.** Say "we ran the comparison at five damage levels", and call the levels relative stress settings.

---

## 3. The other Section II contrasts

### 3.1 Gateway-free, vs Titan [4]: holds at the radio layer
- No node has a special radio role. `is_gateway` is used only to end the trip, to keep trips from starting at a rescue node, in PPO's observation, and to spare rescue nodes in burst failures (`env.py:267, 344`; `timestep.py:299, 306`).
- SOS messages are broadcast with no fixed destination and relayed hop by hop by ordinary nodes (Gossip3 forwarding; context §16).
- Caveat: the routing that was evaluated uses the global snapshot (gap 2, point 4).

### 3.2 LoRa's radio limits, vs [7]: holds
- SF12, 125 kHz, 865 MHz, +20 dBm and −137 dBm sensitivity are in `src/comm/phy.py:14-36`.
- So are the 2.47 s frame airtime and the 6 dB capture rule for collisions.
- Caveats: the model is unvalidated against hardware, and the fast backend has no shadowing.

### 3.3 "Progressive infrastructure failure", vs [7]: does not hold for ABOT either
- Every node is alive at the start of a trip, and the failure rate is 1 per node per hour.
- Trips last a few 10 s steps, so a node on the route dies in only about 1–3% of trips (context §15).
- Burst (area-wide) failures are described in Section III but were never run.
- Why it matters: the paper faults [7] for something ABOT also doesn't test. Leave this contrast off the slide.

### 3.4 Power-aware routing [8]: no contrast to draw
- ABOT's planners don't use battery at all; the route cost is the link score only (`baselines.py:339-342`).
- A battery model exists, but its effect on delivery starts only below 20% charge, which no 10–30 s trip reaches.

### 3.5 IoT systems: holds
- Nothing in ABOT's model depends on internet or cloud. Only the [11] citation is wrong (§1).

### 3.6 Meshtastic, Project OWL, Disaster Radio: holds, with two caveats
1. **Meshtastic's own simulator, Meshtasticator, exists** (outside fact).
   - The paper's claim is about scale for RL, which is narrower, so it can still stand.
2. **ABOT's forwarding resembles Meshtastic's managed flooding** (outside fact; check before quoting). Both rebroadcast, but hold back once they hear others relaying the same message. Yet none of ABOT's baselines is a decentralised protocol (P-10).
   - Why it matters: if asked "how does it compare with Meshtastic?", the honest answer is "not tested yet".

---

## 4. PDR specifically

### 4.1 The cleanest statement of the difference

| | Prior work | ABOT |
|---|---|---|
| Role of PDR | **The outcome:** the share of messages that arrive | **An input:** a link-quality score that steers route choice |
| Examples | [1]: with fewer gateways serving more nodes, delivery falls below 50% in some cases. [7]: better delivery ratio, end-to-end delay and energy | The planner's route cost is 1 ÷ score, and it replans when a node ahead drops below 0.5 |
| What's reported | Delivery (and, in [7], delay) | Link-quality score along the route: 0.267 vs 0.145 |
| What's missing | (ABOT can't tell from the paper) | **No SOS-to-rescuer count and no delay.** This is the next experiment |

### 4.2 Every "PDR" in the paper, and what it actually is

| Where in the paper | What the code computes | Does it show delivery? |
|---|---|---|
| Fig. 2, PDR against distance (V-D) | The channel formulas' chance that one link works at a given distance. Not a run of the mesh (`scripts/make_fig4_pdr_distance.py`) | No: a consistency check of the channel model only |
| "Mean link PDR", 0.267 vs 0.145, and the severity sweep (V-B, V-C) | The per-node link-quality score, averaged over the nodes the route visits. **It is also the dynamic planner's route cost** | No: it shows the routes changed |
| KS-test "PDR" (IV) | The share of SOS messages heard by at least one other node (`timestep.py:382-402`). The two simulators disagree on it | No: being heard once isn't reaching a rescuer |
| "Improved packet delivery" (abstract); "measured delivery gain" (VII) | Nothing. No count of SOS messages reaching a rescue node exists in the code or the results | — |

### 4.3 Why 0.267 can't be read as delivery

- Read as per-hop delivery chances, 0.267 over 3.23 hops gives about 1.4% end to end, and 0.145 over 2.17 hops gives about 1.5% (P-04).
- That is a tie, and both are absurd next to ~100% success.
- So the number is a score, not a share of messages delivered.

### 4.4 Two facts from the committed results that help

1. **Only the planner that actually replans on the score scores higher.** Mean link scores at 10×10, from `FINDINGS.md` §5:

   | Agent | Mean link score |
   |---|---|
   | dijkstra_dynamic | **0.267** |
   | astar_dynamic | 0.166 |
   | astar_static | 0.161 |
   | dijkstra_static | 0.145 |
   | PPO | **0.141** |

   - astar_dynamic has the score in its route cost too, but replans in only 3 of 100 trips, so it stays near the static planners.
   - PPO sees the scores in its inputs and its reward, yet has the lowest score of all.
   - This supports "putting the live score into the route cost, and replanning on it, is what changes routes". It also means PPO gains nothing from link state.
2. **Route length doesn't explain the gap.** The dynamic planner takes longer routes (3.23 vs 2.17 steps), and scores fall as routes get longer, so path length works against it. Matching on route length widens the gap to 1.9–2.6× (paper V-C).
   - Caution: it detours. It is longer than the static planner in 63 of 100 runs, so don't claim the extra hops are "worth it".

### 4.5 One wobble to know about
- The dynamic planner breaks ties between equal routes in an order that depends on Python's hash seed.
- Across 8 seeds, its score ranges from 0.264 to 0.294 (paper V-C).
- So quote "about 1.8×", not a third significant figure.

### 4.6 Say / don't say

| Don't say | Say instead |
|---|---|
| "PDR improved", "better delivery", "the delivery gain" | "Live link-quality scores change which routes get picked: about 1.8× higher scores" |
| "The PDR of the route", or a bare "PDR" | "Link-quality score" for 0.267 / 0.145; "PDR against distance, from the channel model" for Fig. 2 |
| "Routes on continuously updated PDR, unlike failure-triggered approaches" | "Monitors link quality every step and replans when a link degrades, before it fails" |
| "No one routes on live link quality" | "In the disaster-LoRa work we reviewed, routing doesn't use live link quality" |

**If asked "isn't the planner graded on what it optimises?"**
> "Partly, yes. So we only claim that live link state changes which routes get picked. Measuring delivery to a rescuer along those routes is our next step."

**If asked "what do you add over [5] or Meshtastic?"**
> "[5] has hardware results and we don't yet. What we add is routing on live link quality in a gateway-free LoRa mesh, compared at five damage levels, in a simulator fast enough for RL. A head-to-head with Meshtastic is a natural next step, since ABOT is meant to run on the same boards."

---

## 5. Where each number comes from

| Number | Source |
|---|---|
| 0.267 vs 0.145, 1.84×, p = 6.5 × 10⁻⁹ | `results_commaware/FINDINGS.md` §2; paper V-C |
| 0.3098 vs 0.2067, 1.50×, p = 0.0057, n = 43 | `results_commaware/conditional_vc.json`; paper V-C |
| 1.88 / 1.80 / 1.92 / 1.48 / 1.53 by preset | `FINDINGS.md` §2; the paper rounds these to "≈1.8–1.9×" and "≈1.5×" |
| Agent scores 0.267 / 0.166 / 0.161 / 0.145 / 0.141 | `FINDINGS.md` §5 (not in the paper) |
| 1.9–2.6× at matched route length | `FINDINGS.md` §5; paper V-C |
| Hash-seed range 0.264–0.294 | `results_commaware/reproducibility_note.json`; paper V-C |
| 7.2× / 4.7× / 4.0× speed-up (5×5 / 10×10 / 15×15) | Recomputed from `results_rev1/scalability.csv`. The paper's 7.3× is the 5×5 run with no failures |
| KS p = 0.98 (alive nodes), p < 10⁻³ (PDR, delivery count) | `results_rev1/equivalence/ks_table.csv`; paper IV |
| ≈0.28 → 0.218 / 0.216 (dynamic planner's score at severe / extreme) | `results_rev1/damage_severity.csv`; paper V-B |
| < 50% delivery with fewer gateways [1] | Paper I, citing [1] |
| ≥ 99.96% in-range link success, intact–heavy | Derived from the Table I formulas with average path loss (context §15) |
| 1–3% chance a route node dies | Derived from λ = 1/3600 and trip length (context §15) |
