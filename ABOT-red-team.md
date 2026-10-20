# ABOT camera-ready: red-team critique

**Target:** *ABOT: A Decentralized LoRa Mesh Communication Framework for Post-Disaster Environments* (camera-ready docx in this folder, dated 2026-08-30).
**Method:** I read the paper in full, then checked each claim against the code and the committed result files in `<CODE>/darwinV2/`, all read-only. Where a number had to be computed, I re-implemented the code's formulas in small standalone scripts. They are in [`redteam/`](redteam/), they read only committed CSVs and import nothing from `<CODE>`.
**Date:** 2026-10-12.

## The short version, in plain English

A tough reviewer who had read the code would say this:

1. **The simulated messages can't get lost.** When a route takes a hop, the hop always succeeds as long as the next device is still switched on. Radio quality never stops it. That's why every method scores ~100%, and why "worse damage" changes nothing about success.
2. **The "link quality" number in the main result isn't what it sounds like.** It's an average health score for each device the route passes through, not a measure of whether messages got through. The winning method is built to chase that same score, so of course it scores higher on it.
3. **In the fast simulator, every "hello" beacon collides with every other.** All devices send at exactly the same moment. So the "live link state" the paper is built around mostly isn't there. The authors had already spotted and fixed this in their slower simulator, but not in the fast one that produced the results.
4. **The fast simulator leaves out random signal fading.** Up to and including the default "heavy damage" setting, every radio link in range is perfect. The channel-validation figure describes a different, analytic model.
5. **A robot that always presses button 0 performs about as well as the trained AI.** That's because of how the choices are numbered: almost every choice already points toward the two goal corners. Moving the goals to the other two corners would leave the AI no choice that reaches them at all.
6. **The gossip experiment couldn't have found a difference.** During testing, neither version sends any gossip messages.
7. **"7.3× faster" is the smallest-grid number.** At the grid size actually used, it's about 4.7×.

The paper is unusually honest about many of its limits (§14), and that's its best defence. The points above, though, go *beyond* what the paper discloses. Expect at least #1, #2 and #5 from any sharp networking audience. §15 has short, honest answers.

---

**Evidence tags used below**

| Tag | Meaning |
|---|---|
| **[paper]** | Text of the camera-ready paper. |
| **[code]** | `<CODE>/darwinV2/` source, given as `file:line`. |
| **[artifact]** | A committed result file. |
| **[derived]** | Computed in this session by a script in `redteam/`. It either re-implements the code's own formulas or reads committed CSVs. |
| **[ext]** | An outside fact, found by web search or recalled from the literature. **Verify these before quoting them on stage.** |

**Severity**

| Level | Meaning |
|---|---|
| 🔴 Critical | It undermines a headline claim. |
| 🟠 Major | It undermines a secondary claim or the paper's framing. |
| 🟡 Minor | Presentation, citations or wording. |

---

## 0. Executive summary: the ten attacks that hurt most

| # | What the paper says | The attack | Sev. |
|---|---|---|---|
| 1 | Agents reach a safe zone ~100% of the time; severity "removes the mesh's long-range shortcuts" | **Hops never go through the radio channel.** A move succeeds whenever the target neighbour is alive (`env.py:311-313`). Success is at ceiling by construction, at every severity. Agents still use 1,442 m links at "extreme", where the backend's link PDR is 0.0000. | 🔴 |
| 2 | "Removing live PDR … lowers mean link PDR from 0.267 to 0.145" (the supported result) | **The metric isn't link PDR, and it isn't delivery.** It is the average PDR over *all ~30 outgoing links* of whichever node the agent lands on. Links that have never been used count as 1.0. `dijkstra_dynamic` minimises exactly this quantity, so the result is circular. | 🔴 |
| 3 | Link state is derived from beacons heard every 30 s | **In the backend behind every result, every beacon collides.** All nodes beacon in the same propagation round, and the four nearest neighbours tie at 400 m. Zero of 3,068 beacon receptions survive, at every preset [derived]. The authors documented this exact artefact in the SimPy node and fixed it there with jitter (`node.py:263-273`), but not in the timestep backend. | 🔴 |
| 4 | Table I uses σ = 11 dB shadowing; Fig. 2 validates the channel "on the timestep backend" | **The timestep backend has no shadowing.** At intact, moderate and heavy, every in-range link has PDR ≥ 0.9998 [derived]. So *all* the PDR loss at the default preset is from collisions. Fig. 2 was not produced by the timestep backend, despite its caption. | 🔴 |
| 5 | PPO "reaches a safe zone in stochastically fewer steps than the comm-aware Dijkstra planner at both scales" | **A constant policy, "always pick action 0", matches PPO's median and IQR at 10×10**, and it also beats `dijkstra_dynamic` on mean steps at both grid sizes [derived, on the exact evaluation seeds]. | 🔴 |
| 6 | The 8-slot action space handicaps PPO, so its result is a "lower bound" | **The handicap doesn't exist.** Slots are the 8 lowest-ID neighbours, and both safe zones are in row 0, the lowest IDs. Those 8 slots always contain an optimal next hop. If the safe zones were the bottom corners instead, *no* starting node could reach one. | 🔴 |
| 7 | Gossip ablation: on vs off, no difference | **The null is built in.** At evaluation neither arm transmits a single gossip packet, because the value table is always empty. Nothing would read the values anyway. | 🟠 |
| 8 | Each node derives PDR, RSSI and reachability locally from beacons | **The simulator reads all three from ground truth.** PDR comes from the transmitter's view of the simulator's delivery outcome, RSSI is a static mean and reachability is oracle liveness. Beacons carry no sequence number, so the receiver-side PDR the paper describes can't be computed. | 🟠 |
| 9 | Dynamic Dijkstra on live state is the supported routing result | **No mechanism in the protocol spreads link state.** `ROUTE_UPDATE` is never sent, and the planners read the simulator's global snapshot. The decentralised protocol can't implement the planner the result is about. | 🟠 |
| 10 | "Up to 7.3× faster with contention" | 7.3× holds at 5×5 only. **At 10×10, the scale of the experiments, it's 4.7×.** The two backends were also timed running *different agents*. | 🟠 |

Underneath most of these sits a **time-scale mismatch** (§1.4). Episodes last 10–30 simulated seconds, so the 25-minute PDR window, the one-per-hour failure rate, the 300 s battery drain and the "33-minute routing window" never come into play.

---

## 1. The evaluation task doesn't test what the paper says it tests

### 1.1 🔴 Hops are not gated by the channel
- **[code]** `env.py:311-313`: the agent moves to `neighbours[action]` whenever that node is alive. No delivery draw happens and no PDR or PER is consulted.
- **[code]** The neighbour list is the fixed 1,500 m unit-disk graph (`topology.py:96-103`), cached at reset (`env.py:274-278`). It doesn't change with the severity preset.
- **[derived]** (`redteam/per_table.py`) Backend link PDR at grid distances, using mean path loss and no shadowing, exactly as `timestep.py:157-169` does:

| Distance (m) | intact | moderate | heavy | severe | extreme |
|---:|---:|---:|---:|---:|---:|
| 400 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 566 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9501 |
| 800 | 1.0000 | 1.0000 | 1.0000 | 0.9971 | 0.0007 |
| 894 | 1.0000 | 1.0000 | 1.0000 | 0.9427 | 0.0000 |
| 1131 | 1.0000 | 1.0000 | 1.0000 | 0.0258 | 0.0000 |
| 1442 | 1.0000 | 1.0000 | 0.9998 | 0.0000 | 0.0000 |

**Consequences**
- Success is at ceiling because failure is impossible, not because the agents are good. This answers R2's worry ("the very high delivery rates may partly reflect a simplified model") more harshly than R2 put it: success never depended on the channel at all.
- V-D says "Severity therefore bites on the longer links, which is how structural damage removes the mesh's long-range shortcuts." **In the environment that was evaluated, the shortcuts are never removed.** At extreme, a 1,442 m hop with PDR 0.0000 counts as a successful step.

**Best available reply:** "The routing task measures path choice over a live-state graph, not delivery. We should have said that explicitly." **Fix:** gate each hop with Bernoulli(link PDR), or charge ETX retransmissions per hop.

### 1.2 🔴 The routing agent doesn't carry the SOS message, and SOS delivery is never reported
- **[code]** SOS packets are injected from *random* alive nodes (`env.py:390-409`). The simulator then propagates them with Gossip3 and geo-greedy forwarding (`timestep.py:476-590`), whatever route the agent picks. The agent is a token walking the graph.
- **[code]** The +5 reward fires if *any* new delivery happened *anywhere* in the network (`env.py:336-337`).
  - **[artifact]** It fired in **100/100** timestep episodes (`results_commaware/FINDINGS.md` §1), so it is a constant offset with no learning signal.
  - The paper's reward-balancing paragraph still treats it as shaping.
- The system's stated purpose is propagating distress signals to a rescue node. **The paper never reports how often an SOS reaches a rescue node, or how long it takes.**
- The "PDR" in the KS test is `network_pdr`: the fraction of injected messages that reached *at least one node other than the origin* (`timestep.py:382-402`). One neighbour hearing the message counts as a delivery.

### 1.3 🟠 The task is 1–3 hops
- **[derived]** `redteam/seed_starts.py` reproduces the start nodes of evaluation seeds 0–99. Gymnasium's `np_random` is `default_rng(seed)`, and the start is its first `integers` draw.
- Optimal hop counts on those starts: **{1: 23, 2: 37, 3: 40}**, mean 2.17. This matches the three fastest planners' committed step distribution exactly (`results_commaware/commaware_main_10x10.csv`), which validates the reproduction.
- So **23% of the "routing" episodes are a single hop**, and no optimal route at 10×10 is longer than 3 hops.
- Both safe zones are fixed and never vary: `N000` and `N009`, the two top corners (`topology.py:135-151`, `corners[:count]`).

### 1.4 🔴 Time-scale mismatch: the motivating dynamics barely act inside an episode

| Mechanism | Time scale in the model | What happens in an evaluated episode (10–30 s simulated) |
|---|---|---|
| Episode cap | 200 steps = 2,000 s, "a representative post-disaster routing window" [paper] | Reached only by the livelocked episode. Typical episodes last 1–3 steps. |
| Beacons | every 30 s, all nodes at once (`timestep.py:452-472`) | The first beacon round is injected during the advance at step index 1 (t = 20→30 s). **Episodes of ≤ 2 steps make every decision before any beacon:** 60% of the fastest planners' episodes, 47% of PPO's and 31% of `dijkstra_dynamic`'s [artifact step distributions]. |
| PDR window | 50 samples, "≈ 25 min" [paper] | Never fills. It holds 1–2 SOS floods and at most one beacon round. |
| Node failure | λ = 1/3600 s⁻¹ per node | P(a given node fails within 30 s) ≈ 0.8%. That is about 0.4 sudden deaths per 100-node episode [derived]. Graceful failures need 300 s to kill a node. |
| Battery scaling | only below 20% charge, i.e. ≥ 240 s into a graceful drain | **Never triggers.** |
| Burst / spatially correlated failure | implemented | **Never evaluated** (every run uses `mixed`), although the Introduction motivates the work with "spatially correlated failure patterns". |
| λ_fail sweep for the speedup | {0, 1/3600, 1/1800} | "Moves neither figure" is trivially true, because there is almost nothing for failures to do. |

---

## 2. The headline PDR metric

### 2.1 🔴 What "mean link PDR" actually is
- **[code]** The column is named `mean_pdr_seen` (`results_commaware/run_commaware.py:127-135`). It is the mean over steps of `info["pdr"]`, which is `mesh_state[agent_node]["pdr"]` *after* each move (`env.py:340, 355`).
- **[code]** `mesh_state[n]["pdr"]` is the **mean over all of node n's outgoing neighbour links** of each link's window mean, with **1.0 for any link that has never been used** (`timestep.py:728-733`).
- It is therefore not the PDR of the links the path used, and not end-to-end delivery. It is a node-health score of the nodes visited.

### 2.2 🔴 The result is circular
- **[code]** `dijkstra_dynamic` sets edge cost = 1 / max(mean(PDR_u, PDR_v), 0.01), using the *node* scores (`baselines.py:339-342`). It replans if any of the next 3 nodes scores below 0.5 (`baselines.py:312-320`).
- It minimises the very quantity the metric averages. "Removing live PDR from the edge cost lowers mean PDR" therefore says "removing the objective lowers the objective."

### 2.3 🔴 A high score means a node stayed quiet
Untested links count as 1.0, and every reception in a beacon round fails (§4.2). A node's score is therefore high mainly if it **hasn't transmitted yet**, or transmitted only in rounds without contention.
- **[derived]** `redteam/pdr_dist.py` on the committed CSVs shows the per-episode values bunching at exact numbers:
  - 26 of 100 `dijkstra_static` episodes are exactly 0.0, and its median is 0.043;
  - the most common `dijkstra_dynamic` value is exactly 0.5 (8/100 episodes), e.g. one step at an untouched node (1.0) and one after the beacon wipe (0.0).
- The "live link quality" the planner exploits is in effect "which nodes were silent, or collided least, in a synchronised flood."

### 2.4 🟠 Averaging the per-hop values hides how loss compounds over hops
Suppose these were real per-hop delivery probabilities. End-to-end delivery would then be about 0.145^2.17 ≈ 1.5% for the static arm and 0.267^3.23 ≈ 1.4% for the dynamic arm.
- That is roughly a tie.
- Both figures are absurd next to 100% task success.

This is illustrative only, since §2.1 shows the metric isn't per-hop PDR. But a reviewer who takes the paper at its word will do this arithmetic.

### 2.5 🟠 "Mean PDR falls with path length" is a clock effect
Longer episodes include more steps after the t = 30 s beacon wipe. The matched-on-steps comparison ("1.9–2.6×") is matching on time elapsed as much as on route.

### 2.6 🟠 "PDR" means three different things, and none of them is SOS delivery
1. **Fig. 2:** analytic PDR averaged over shadowing (`scripts/make_fig4_pdr_distance.py`).
2. **V-B and V-C:** the node-average outgoing link score of §2.1.
3. **The KS test:** `network_pdr`, i.e. message reached ≥ 1 other node.

The abstract's "improved packet delivery performance" doesn't correspond to any measured quantity.

### 2.7 🟠 The absolute value depends on the backend
- **[artifact]** On the same static paths, the SimPy run gives 0.057 and the timestep run gives 0.145, a 2.5× difference (`results_rev1/baselines.csv` vs `results_commaware/commaware_main_10x10.csv`).
- The 1.8× ratio has **never been measured with both arms on SimPy**, so "the separation survives a change of simulator" is untested.

---

## 3. Channel model and physics

### 3.1 🔴 The backend behind every result has no shadowing
- **[code]** `timestep.py:157-169` builds a per-edge PER from the *mean* path loss, and its own comment says "no shadowing". The delivery roll uses that cached PER (`:517-526`).
- **[code]** The docstring at `channel.py:185` claims "Shadowing randomness is captured by the per-packet Bernoulli draw." That's wrong: a Bernoulli draw on the mean PER is not the average over shadowing, because the PER curve is non-linear.
- **Consequences:**
  1. Half of every severity preset (σ) has no effect.
  2. Under the default preset, heavy, the channel loses nothing on any in-range link (table in §1.1).
  3. V-B's "near 0.28 across intact, moderate and heavy, then a step" is the backend having **no channel loss at all up to heavy**. At severe, links over ~1 km fall off a cliff (1,131 m: 0.026), and the "step" is that cliff.
  4. Fig. 2's operating-range numbers don't describe the simulated links. The paper's "above 0.73 at 400 m under every preset" is 1.000 in the backend at every preset.

### 3.2 🟠 The Fig. 2 caption is wrong
The caption says "timestep backend". The figure's own script says it "does NOT run a mesh simulation (SimPy / TimeSteppedProvider)" (`scripts/make_fig4_pdr_distance.py:15`). It queries the analytic `LoRaChannel`, *with* shadowing.

### 3.3 🟠 The "step at severe" coincides with a second discontinuity
- The capture threshold is 6 dB.
- **[derived]** The RSSI gap between a 400 m and a 566 m (√2) transmitter is 10·n·log10(√2) = 1.505·n dB. That is 5.72 dB at heavy (all frames collide) and 6.32 dB at severe (the stronger frame is captured).
- So capture behaviour between first- and second-ring neighbours flips **exactly between heavy and severe**.
- The paper reads the step as damage behaviour, without ruling out either of these model artefacts.

### 3.4 🟠 The presets aren't calibrated, and "intact" is beyond physics
- **"intact"** (n = 2.7 from d₀ = 1 m) gives a PDR = 0.5 range of **45.5 km** for ground-level handhelds. **[ext]** That is past the radio horizon of antennas 1–2 m above ground (roughly 8–10 km between two such antennas). It also ignores ground reflection: a two-ray model loses about 40 dB/decade (n ≈ 4) beyond a breakpoint of only tens of metres at these heights, even in open terrain.
- **[ext, verify]** LoRaSim's measured urban model, widely reused, is PL(40 m) = 127.41 dB with exponent 2.08. It gives 156.5 dB at 1 km.
  - ABOT's *heavy-collapse default* gives 145.2 dB at 1 km, about **11 dB more benign than that undamaged-city model**.
  - "intact" gives 112.2 dB, 44 dB more benign.
  - Under LoRaSim's model, ABOT's own 157 dB link budget reaches only ~1.06 km, which is less than the 1,500 m neighbour radius.

### 3.5 🟡/🟠 The path-loss citation doesn't support the numbers
- **[paper]** The exponent is "based on IEEE 802.15.4a CM6 measurements and post-earthquake LoRa field data [10]".
  - But [10] *is* the 802.15.4a final report.
  - The post-earthquake data is cited only in a code comment (Ferreira et al. 2020, `phy.py:47`), never in the paper.
- 802.15.4a is a UWB channel model, measured mostly over tens of metres.
- **[code]** The code calls CM4 "outdoor NLOS" (`phy.py:46`).
  - **[ext, verify]** In 802.15.4a's numbering, CM4 is office NLOS and CM6 is outdoor NLOS.
  - From memory, neither parameter set is close to n = 3.8, σ = 11 dB. Check table 1 of IEEE 802.15-04-0662 before defending this choice.

### 3.6 🟡 Other modelling gaps
- Per-link PER and RSSI are static for the whole episode: no fading, no temporal correlation.
- There is no mobility, although Section III says the mesh reconfigures "as nodes fail or move out of range".
- The neighbour set is fixed by the 1,500 m disc, whatever the preset. At extreme, "reachable neighbours" still counts nodes that can't be heard.

---

## 4. MAC and protocol design

### 4.1 🔴 The design saturates its own channel, whichever backend you use
- **[derived]** The mean degree is 30.7. A beacon's time on air at SF12 is 1.32 s for a 20 B frame, which is the paper's 4.4% figure. With the paper's 34 B header plus the 4 B node ID it is 1.97 s, and that is what the SimPy reference puts on air (`node.py:433`).
- Each receiver therefore sees an offered load **G ≈ 1.35–2.0 Erlang from beacons alone**.
- Under pure ALOHA without capture, a frame survives with probability about e^(−2G) ≈ 2–7%.
- With SF12, 30 s beacons and ~30 neighbours, the channel is saturated before any SOS traffic exists. Beacon-based link monitoring can't work at this density.

### 4.2 🔴 The timestep backend synchronises every beacon, an artefact the authors had already identified
- **[code]** `timestep.py:452-472` injects every node's beacon at the exact 30 s boundary, into one round.
- **[derived]** `redteam/beacon_round.py`: with all nodes alive, **0 / 3,068 receptions survive at 10×10 and 0 / 7,848 at 15×15, at every preset.** Each receiver's two strongest transmitters are equidistant, so the capture margin is 0 dB.
- **[code]** The SimPy node's own docstring (`node.py:263-273`) says that without jitter "the 6 dB capture rule then rejects ALL beacons at every receiver forever — a synchronisation artifact, not channel physics." The jitter fix went into SimPy only.

### 4.3 🟠 "Slotted ALOHA" doesn't fit a gateway-free mesh
- Slotted ALOHA needs network-wide slot synchronisation. **[ext]** Polonelli et al. [2] take that synchronisation from the LoRaWAN gateway.
- ABOT has no gateway and describes no time-sync mechanism.
- In the timestep backend, a "slot" is a whole propagation round: one BFS layer of a flood, made of frames that each last 1.3–2.5 s.
- Capture is decided on mean RSSI alone, with no timing (preamble-lock) condition.

### 4.4 🟠 Forwarding as described ≠ forwarding as simulated
- **No random forward timer.** The paper describes one, but in the timestep backend all forwarders transmit in the same round, and suppression counts only duplicates from earlier rounds (`timestep.py:500-505`).
- **No half-duplex.** Nodes transmit and receive in the same round.
- **The ~25% saving is tautological.** "Saving roughly 25% of a full flood's transmissions" simply restates p = 0.75. It wasn't measured, and p and K were never ablated. With degree ~30, far smaller p would also work; Haas et al.'s thresholds come from much sparser graphs.

### 4.5 🟠 The packet format is simulator bookkeeping
- **[paper]** "Packet headers are a 34-byte binary struct."
- **[code]** `packet.py:8-14` says those 34 bytes are "simulator bookkeeping metadata … never actually put on the air. The real DARWIN-Comm wire protocol has a compact ~9-byte header". That 9-byte header is specified nowhere.
- The struct carries a float32 RSSI field, which is a receiver-side measurement and makes no sense to transmit.
- Taking the paper's 34 B header at face value, a gossip frame is 76 B, which exceeds the 51 B MTU the paper cites.

### 4.6 🟠 The MTU is a LoRaWAN rule borrowed by a protocol that isn't LoRaWAN
- 51 B is LoRaWAN's DR0 MAC-payload limit (`phy.py:17`). Raw LoRa allows 255 B.
- The paper sells itself as "unlike conventional LoRaWAN", then sizes its gossip payload to a LoRaWAN regional parameter.

### 4.7 🟠 The duty-cycle limitation is miscalculated and cites the wrong jurisdiction
1. **The arithmetic.** 4.4% = 1.32 s / 30 s, which is a 20 B frame (`config.py:41` says "a 20-byte beacon"). With the paper's own 34 B header, the beacon alone is **6.0–6.6%**, before SOS relays and gossip.
2. **The jurisdiction.** ETSI EN 300 220-2 is a European standard. The paper chose India's 865–867 MHz band precisely for its Indian licensing.
   - **[ext, verify]** LoRaWAN Regional Parameters reportedly set *no* duty-cycle limit for IN865. India's rules (GSR 564(E), now GSR 853(E)) cap power at 1 W / 4 W ERP.
   - Either the limitation is misattributed, or it applies to a different country.
3. **The wrong quantity.** The paper conflates per-device duty cycle with "channel occupancy". Occupancy at a receiver is about 30× the per-device figure (§4.1).

### 4.8 🟠 The routing layer the paper evaluates can't run on the protocol it describes
- **[code]** `ROUTE_UPDATE` and `ACK` are defined (`packet.py:37-42`) but never sent anywhere in `src/`.
- Beacons carry only the sender's ID.
- The evaluated planners read the simulator's global snapshot (`runner.py:94-96`) and oracle liveness (`baselines.py:330-333`).
- Running Dijkstra on live global state in a gateway-free mesh would need link-state flooding, like OLSR's TC messages, on a channel that is already saturated (§4.1). **The protocol cost of the paper's supported result is never modelled. As evaluated, the result holds only for an oracle planner.**

---

## 5. Link-state monitoring: described vs simulated (🟠)

| Paper (Section III, Link-State Monitoring) | What the code does |
|---|---|
| "Each receiver derives all three locally from the beacons it hears" | Nothing is derived from what a receiver hears. |
| PDR "from arrival statistics over a sliding window of 50 packets" | Taken on the **transmit side**, from the simulator's own record of whether each attempt was delivered (`timestep.py:538-545`; SimPy `_record_tx`, `node.py:458-481`). It counts every attempt, flood relays included, not only beacons. A broadcast sender can't know this without ACKs, and a receiver can't count misses because beacons carry no sequence number. |
| "≈ 25 min" window | Holds 50 attempts on one directed link, from any traffic. Never filled within an episode (§1.4). |
| RSSI "from the received frame" | A static mean RSSI per edge, with no shadowing (`timestep.py:739-743`). |
| Reachability "from the fraction of known neighbours heard recently" | The **count** of neighbours that are alive in the simulator (`timestep.py:736`). Oracle knowledge, and not a fraction. |
| "the eight neighbor PDRs" in the observation | The node-average score of each of the 8 lowest-ID *alive* neighbours (`state.py:134-138`), not the PDR of the link to them. |

---

## 6. The RL component

### 6.1 🔴 A constant policy matches PPO
**[derived]** `redteam/seed_starts.py` plays the evaluation seeds' exact start nodes. It ignores failures, which hit a given node with probability ≈ 1% per episode, so the constant-policy numbers are slightly optimistic.

| Policy | 10×10 median [IQR] | 10×10 mean | 15×15 median [IQR] | 15×15 mean |
|---|---|---|---|---|
| Optimal, i.e. the three fastest planners | 2 [2, 3] | 2.17 | 3 [2, 4] | 3.20 (paper: 3.23–3.25) |
| **PPO** [paper] | **3 [2, 3]** | **2.48** | **4 [3, 4.25]** | **3.56** |
| **Always action 0** (no learning, no observation) [derived] | **3 [2, 3]** | **2.71** | **4 [4, 5]** | **4.07** |
| `dijkstra_dynamic` [paper] | 3 [2, 4] | 3.23 | 4 [3, 6] | 4.40 |

- PPO beats the constant policy by 0.23 and 0.51 mean steps, so it learned *something*. But **its only significant win, over `dijkstra_dynamic`, is also achieved by a policy that ignores its input.**
- This fits the livelock story, "a dead action-0 target is re-selected indefinitely".
- It also fits the policy's near-zero entropy: final entropy ≈ 0.24–0.33 nats against ln 8 = 2.08 (`results_rev1/convergence_summary.json`).
- **[derived]** For scale, a uniformly random choice over the 8 slots needs a mean of 11.5 steps at 10×10 (`redteam/random_policy.py`).

### 6.2 🔴 The action encoding points at the answer
- **[code]** Node ID = row·cols + col (`topology.py:49-57`). The actions index the ID-sorted neighbour list (`env.py:274-278`).
- So the 8 lowest-ID neighbours always lie 2–3 rows *up*. For example, node N055's slots are N023–N027 and N032–N034.
- **[code]** The safe zones are `corners[:2]`, i.e. (0, 0) and (max_x, 0): **both in row 0** (`topology.py:135-151`).
- **[derived]** (`redteam/action_geom.py`)

| | 10×10 | 15×15 |
|---|---|---|
| Share of the 8 slots that move closer to the nearest safe zone | 85% | 88% |
| Share that move toward row 0 | 89% | 93% |
| Optimal hops using only the 8 slots (all nodes alive) | equal to the full-graph optimum at **every** start node | same |
| **If the safe zones were the two bottom corners** | **0 / 98 starts could reach any safe zone, under any policy** | **0 / 223** |

### 6.3 🔴 So the "lower bound" framing fails on its own terms
The paper names two asymmetries that run against PPO. Neither holds up.
- **Asymmetry 2, the 8 slots, costs zero hops** with this safe-zone placement (§6.2).
  - **[artifact]** `results_rev2/action_space_audit.json`: `astar_dynamic`, whose paths match the static planners', used a slot beyond 8 in **1 of 217** actions.
  - Only `dijkstra_dynamic` used out-of-range slots (23.6% of its actions), and it's the planner PPO beats.
  - The comparisons PPO *loses* are unaffected by truncation.
- **Asymmetry 1, a local versus global view, is overstated.**
  - PPO's observation includes a **global BFS hop count** to the nearest alive gateway, computed over the whole alive graph (`state.py:164-166, 190-222`).
  - It also includes global gateway liveness (`state.py:146-150`).

### 6.4 🟠 Much of the observation is constant
- The reachable count/8 (`state.py:106-108`) and density/8 (`:168-169`) are clipped at 1, and every node has degree ≥ 14, so both are **always 1.0**.
- Battery is ≈ 1.0, since the drain never reaches it.
- Elapsed fraction is ≤ 0.015.
- Maximum neighbour RSSI always comes from the 400 m neighbour, so it is constant within a preset.
- Before the first beacon round, the neighbour-PDR slots are mostly 1.0 (untested links).

### 6.5 🟠 The headline results come from one trained network, and the least converged one
- **[code]** Table II and the severity sweep load only `ppo_10x10_seed0.zip` (`scripts/run_monte_carlo.py:53`, `scripts/run_damage_severity.py:63`).
- That is the seed whose critic's explained variance is −0.67, the worst of the three, the one the paper says "clearly hasn't converged".
- The paper doesn't say which seed it evaluated.
- The p-values treat 100 episodes as samples of "PPO", but the variance *between training runs* is never measured. This is the standard criticism in Henderson et al. 2018 and Agarwal et al. 2021 [ext].

### 6.6 🟠 The 15×15 PPO result is the 10×10 model applied zero-shot, and the paper doesn't say so
`run_monte_carlo.py:53, 60`.

### 6.7 🟠 Training saturates almost at once
- **[artifact]** `convergence_summary.json`: PPO reaches 90% of its final reward after **1,400–15,400 steps out of 200,000**, i.e. 1–11 PPO updates.
- That is what a near-trivial task looks like.

### 6.8 🟠 The livelock rests on one episode, and its mechanism isn't in any artifact
- Block 3 has success 0.98, i.e. 1 failure in 50. Overall success of 0.996 at each preset is 1 in 250.
- It's the **same seed at every preset**: one scenario replayed five times, not five separate events.
- **[artifact]** `results_rev2/seed3_outlier.json`: per-episode data is "not recoverable".
- **[artifact]** `<CODE>/AUDIT-RERUN.md` §7, item 12: there is no artifact for the step-by-step story.
- The paper nevertheless states the mechanism ("a dead action-0 target is re-selected indefinitely") as fact.

### 6.9 🟡 The livelock comes from the environment's design, not from the size of the action space
- The environment keeps dead neighbours addressable (`env.py:380-388`) and applies −20 with no change of state. Action masking would fix it in a few lines.
- Calling it an "action-space truncation" problem misplaces the cause.

### 6.10 🟡 Smaller RL inaccuracies
- **The +5 term:** "+5 per new SOS delivered" is really "+5 once per step if anything was delivered anywhere" (`env.py:336-337`), and in practice it fires every step (§1.2).
- **The Introduction:** it says PPO is "intended to replace the Dijkstra solver", but nothing in the results supports replacing it, and the policy depends on a global BFS feature (§6.3) that a single node couldn't compute.

---

## 7. Baselines

### 7.1 🟠 None of the baselines is decentralised
- All four planners get oracle global liveness and the global PDR snapshot.
- The paper's pitch is gateway-free decentralisation, yet it evaluates **no decentralised routing protocol**:
  - pure flooding;
  - Gossip3 on its own (ABOT's own forwarding);
  - Meshtastic managed flooding;
  - AODV or DSR;
  - OLSR, B.A.T.M.A.N. or Babel with ETX;
  - greedy geographic routing (GPSR).
- Greedy-geographic forwarding is *part of ABOT's own forwarding scheme* and still isn't used as a baseline.
  - **[derived]** Restricted to PPO's 8 slots, a geographic-greedy rule is optimal from every start.

### 7.2 🟠 The A* heuristic isn't admissible
- **[code]** The heuristic is Euclidean distance **in metres**, i.e. hundreds to thousands (`baselines.py:227-229, 452-469`).
- It is added to edge costs of 1 per hop (static) or 1/PDR in the range 1–100 (dynamic).
- So A* degenerates to greedy best-first search, and the PDR weights barely matter.
  - This explains the "uninformative A* pair" better than "the replan trigger rarely fires" does.
- The docstring claims the heuristic is admissible (`baselines.py:367-369`).

### 7.3 🟠 The "PDR-weighted edges" are weighted by node, not by link
- An edge's cost comes from the two *endpoints'* average scores (`baselines.py:339-342`).
- So from a given node, the planner can't prefer a 400 m link over a 1,442 m one.

### 7.4 🟡 A silent fallback to action 0
- `_node_to_action` returns 0 whenever the planner's target isn't a neighbour (`runner.py:153-159`). That is a *valid* move to the lowest-ID neighbour, not the invalid action its docstring says.
- When a static planner's plan breaks, it is therefore quietly steered "up-left", toward the safe zones.
- This is rare, because failures are rare.

---

## 8. Statistics

1. 🟠 **Unpaired tests on paired data.**
   - Every agent runs the same 100 seeds, with the same start node and the same failures.
   - A Wilcoxon signed-rank or sign test is the right choice. Mann–Whitney (`stats.py:271-272`) ignores the pairing.
   - The same applies to the 43-seed analysis.
2. 🟠 **There is one trained network** (§6.5).
3. 🟠 **The Holm family contains near-duplicate tests.**
   - At 10×10, `astar_static`, `dijkstra_static` and `astar_dynamic` have *identical* step distributions ({1: 23, 2: 37, 3: 40}), so one test is counted three times.
   - The "PPO worse" verdict rests on p_corr = 0.047.
   - At 15×15, "no difference" is absence of evidence at n = 100. The effect points the same way as at 10×10 (r_rb = +0.137, favouring the planners), yet the paper writes "indistinguishable".
4. 🟠 **The 43-seed subset is post hoc.**
   - Which seeds are in it depends on `PYTHONHASHSEED` (`results_commaware/FINDINGS.md` §2, §4).
   - p = 0.0057 is uncorrected.
   - The static arm's PDR on the subset is 0.2067, against 0.145 overall, so the subset differs systematically from the full sample.
   - The paper calls it "the cleanest" number.
5. 🟡 **The 1.8–1.9× ratios have no confidence intervals.** They are single point estimates under one hash seed, and the dynamic arm alone ranges 0.264–0.294 across hash seeds.
6. 🟡 **The Pearson r of −0.987 to −0.993 between reward and steps is an identity, not a finding.** Reward = 100 − steps − a small PDR term + a constant 5 (FINDINGS §1: residual 0.0).
7. 🟡 **The ablation's sample size is worded ambiguously.** "3 seeds and 300 episodes per arm" means 3 × 100 = 300 per arm (`gossip_ablation_summary.json`).

---

## 9. Simulation backend and speedup

### 9.1 🟠 The headline speedup is quoted at the wrong scale
**[derived]** (`redteam/speed.py` on `results_rev1/scalability*.csv`)

| Grid | Contention on (every result) | Contention off |
|---|---:|---:|
| 5×5 | **7.2×** | 36× |
| 10×10 (the experiments) | **4.7×** | 137× (mean) / 150× (median) |
| 15×15 | 4.0× | 294× (mean) / **303× (median)** |
| 20×20–30×30 | 3.5–4.5× | SimPy times out |

- "Up to 7.3×" is true only at the smallest grid, which no experiment used.
- 303× applies to a mode (contention off) that no result uses.

### 9.2 🟠 The two backends were timed running different agents
- **[code]** SimPy runs `CommAwareDijkstraBaseline`, a legacy planner not in the paper. The timestep backend runs `DynamicDijkstraBaseline` (`scripts/benchmark_scalability.py:104` vs `:185`).
- Wall time includes planner overhead, and the episodes differ in length: mean reward at 10×10 is about 97 on SimPy against about 100 on timestep.

### 9.3 🟠 The premise for the new backend is weak
- With contention on, a 10×10 SimPy episode takes 0.17 s.
- 200k steps is roughly 80k short episodes, about 3–4 CPU-hours on one core, and under an hour across the 7 workers used.
- SimPy with contention ran up to 30×30 (one timeout).
- "Could not supply enough environment steps" isn't shown.

### 9.4 🟠 The equivalence argument proves little
- Equal alive-node counts are close to guaranteed: both backends run the same failure model, and failures don't depend on traffic. That says nothing about the network simulation itself.
- For delivery count, the KS statistic is **1.0** at 10×10 (`results_rev1/equivalence/ks_table.csv`): the two distributions don't overlap at all. "p < 10⁻³" understates this.
- **[paper]** "equivalence holds for liveness, what the agent trains against". But the agent's observation is built from PDR features, and PDR is exactly what *isn't* equivalent.

---

## 10. Q-value gossip

1. 🟠 **At evaluation, neither arm sends a single gossip packet.**
   - `GossipScheduler.inject` returns immediately when its table is empty (`gossip.py:200`).
   - A fresh scheduler with an empty table is created at every reset (`env.py:280-288`).
   - The evaluation path never fills it (`scripts/run_gossip_ablation.py:136-150`, then `runner.run_episode`).
   - So the "on" arm evaluates in exactly the same environment as "off". The paper's "the enabled arm pays gossip's airtime" is false at evaluation.
2. 🟠 **During training, gossip almost never transmits once episodes get short.**
   - The callback pushes the table at the end of each rollout (`ppo_trainer.py:136-140, 170-203`), into a scheduler that is replaced at the next reset.
   - Gossip is injected only at steps 0, 5, 10… of an episode, and the table is still empty at step 0. With 1–3-step episodes, a non-empty table almost never reaches step 5.
3. 🟠 **Nothing reads the values.** The merge isn't wired in and no observation feature uses them. The two arms are almost the same training process, so the null result is guaranteed. Calling this an ablation of "Q-value gossip" overstates it.
4. 🟡 **The "Q-table" has no clear meaning.**
   - V(s) depends on elapsed time, PDR and other inputs, but it is averaged per node.
   - The node is recovered from the observation's (x, y) by nearest-position lookup (`ppo_trainer.py:212-254`).

---

## 11. Novelty and related work

1. 🟠 **Live link-quality routing is ETX.**
   - **[ext]** The 1/PDR edge cost is one-directional ETX (De Couto et al., MobiCom 2003).
   - OLSR with ETX (olsrd's link-quality extension), B.A.T.M.A.N. (TQ, from OGM receipt statistics) and Babel (RFC 8966) all update link quality continuously from hello statistics.
   - Gap 2 ("routing acts on static topology or failure-triggered recomputation") is contradicted by twenty years of mesh-routing work, none of which is cited.
2. 🟠 **Simulators with RL interfaces already exist.**
   - **[ext]** ns3-gym (Gawłowicz & Zubow 2019) provides a Gym interface to ns-3, which has a LoRaWAN module (Magrin et al.). FLoRa (OMNeT++), LoRaSim and Meshtastic's own Meshtasticator also exist.
   - Gap 1 is backed by [11], which itself builds a DRL environment for LoRa.
3. 🟠 **The closest prior work has stronger evidence.**
   - [5] (Arregui Almeida et al. 2025) is a gateway-free, self-healing LoRa mesh on ESP32, *with hardware results*.
   - The paper never states what ABOT adds over [5] or [6]. On evidence, ABOT, which is simulation only, is behind them.
4. 🟡 **RL routing literature is missing entirely:** Q-routing (Boyan & Littman 1994) and DRL routing work in WSNs, FANETs and LoRa [ext].
5. 🟡 **Meshtastic is cited as a platform, never as a baseline.** Gossip with duplicate suppression is close to Meshtastic's managed flooding.
6. 🟡 **The evaluation is centred on gateways.** Each episode routes to one of two fixed sinks that the code calls `is_gateway`, and the observation includes the "direction to the nearest alive gateway". That sits awkwardly with "operates without centralized gateways".

---

## 12. Framing and internal consistency (🟠 unless marked)

- **Abstract, "improved packet delivery performance under moderate infrastructure degradation".**
  - No result is specific to "moderate".
  - `dijkstra_dynamic`'s score is flat from intact to heavy.
  - The comparison is against an ablated planner, not against any existing system.
- **Abstract, "limitations of RL-based routing under extreme network collapse".** V-B says PPO is flat across presets, and the outlier block is just as bad at *intact* (16.9). **The abstract contradicts the results.**
- **"a device with a LoRa radio module"** (Introduction), against "framework" (abstract) and "protocol" (III). No device was built.
- **"three functional layers"** in the text, against "Four Layer" in the Fig. 1 caption. 🟡
- **"a representative post-disaster routing window" (33 min).** Real episodes last 10–30 s (§1.4).
- **"steps-to-safe-zone are identical on all 100" (V-C, first paragraph).** This reads as static vs dynamic, which is contradicted two sentences later (3.23 vs 2.17). In the artifact, it means the static planners' steps are the same on SimPy and on timestep (FINDINGS §1).
- **"any separation … comes from replanning alone" (V-C).** The same paragraph then restricts to the 43 of 100 seeds where the first routes coincide, conceding that in the other 57 the routes differ for another reason (hash tie-breaking).
- **"0.267 to 0.145 … over 250 episodes per preset per arm".** The 0.267 / 0.145 figures come from the 100-episode main run; 250 per preset is the severity sweep. 🟡
- **"Severity … removes the mesh's long-range shortcuts" (V-D).** It doesn't, in the environment that was evaluated (§1.1).
- **"multi-kilometre range … without repeaters".** The PDR = 0.5 range is 2.0 km at the heavy default, 1.03 km at severe and 637 m at extreme.
- **"non-stationary, spatially correlated failure patterns".** Burst failures were never evaluated.
- **Conclusion, "the ablations locate the measured delivery gain in live link state alone".** No delivery was measured (§2.1).
- **Formatting.** In VI, the duty-cycle and action-space items are run together into one paragraph. 🟡

---

## 13. Citations, numbers and wording (🟡 unless marked)

- 🟠 **[3]: "6.7 million deaths in the 1990s".**
  - **[ext, verify]** EM-DAT-based summaries put 1990s natural-disaster deaths **below about 0.8 M**, and Our World in Data puts a typical recent year at 10–20k.
  - The figure is probably misquoted, perhaps from a different period or metric. **Check [3] before the talk.**
- **"Al-Hadhrami et al. [8]":** [8] is Olajide (PARA, PLoS ONE 2018).
- **[11]:** cited for IoT situational awareness and for the simulator gap, but it's a DRL LoRa transmission-policy paper.
- **[10]:** cited for "post-earthquake LoRa field data", but it's the 802.15.4a report. The paper says CM6, the code says CM4.
- **Reference formatting:** [4] reads "15 Oct.15, 2024"; [1] reads "pp. 14"; check that [12]'s 2026 date is right.
- **Typos:**
  - the keywords line contains ", ,";
  - "dept. Of";
  - "amplified the damage to more damaging effects";
  - "regime. with";
  - "(p = 0.886). which";
  - "(p = 0.0057,r_ rb";
  - "n_ PL";
  - "Haas et al. [9] shows";
  - "uses Stable-Baselines3 PPO as default hyperparameters";
  - "42 Byte".
- **Table II's caption** is split across two paragraphs.
- **Table I** lists σ = 11 dB as a model parameter, but the backend behind the results doesn't use it (§3.1).
- **Figures:** the paper has only two, and neither shows the main results. Table II carries them alone.

---

## 14. What survives the attack

These points are fair to the paper, and worth knowing for the talk:
- **The paper is unusually candid.** It says plainly that:
  - validation is simulation only;
  - PPO isn't better;
  - the merge is unwired;
  - the KS tests fail on PDR;
  - ties depend on the hash seed;
  - the A* pair is null;
  - the critic didn't converge.
  Reviewers rewarded that, and two of the three nominated it for best paper.
- **The infrastructure is real.** The two backends, the Gym environment, the statistics pipeline and an audit trail that re-derives the numbers all exist.
- **A narrow true claim remains:** a replanning planner that consumes a live per-node health signal visits nodes that score higher on that signal, inside a model where the signal mostly reflects contention. That supports "the pipeline works end to end", not "live link state improves delivery".
- **The livelock diagnosis points the right way.** Dead neighbours shouldn't stay addressable, and action masking is the right fix.

**Narrowest defensible version of each headline claim**

| Claim | Narrowest defensible version |
|---|---|
| Live link state is where the gain is | In simulation, a planner that replans on a live per-node health score reaches nodes with higher scores. Delivery itself wasn't measured. |
| PPO | A PPO policy trained on this environment reaches the sink in a similar number of hops to the planners. The environment needs harder tasks and randomised sinks before any comparison means much. |
| Backend | 4–5× faster than our SimPy reference at the scales evaluated. The two backends agree on node liveness, not on traffic. |
| Gossip | Transport is implemented. Nothing has been evaluated yet. |

---

## 15. Q&A drill: the hardest questions and the shortest honest answers

1. **"If a hop never fails, what does 100% success mean?"**
   That the planners always find a path over the live-state graph. Delivery over that path isn't simulated in the routing task. Gating hops by link PDR is the first thing we'd change.
2. **"Your 'link PDR' averages over links that were never used. Isn't the 1.8× just the planner optimising its own metric?"**
   Partly, yes. The metric is a node-level health score, and the dynamic planner uses it as its edge cost. The honest reading is that the live signal changes routes, not that it improves delivery.
3. **"Why does a constant action match PPO?"**
   Neighbour slots are ordered by ID, and both safe zones are in the lowest-ID row, so most slots point toward them. Randomising sink placement and masking actions are the fixes. PPO still beats the constant policy by about 0.2–0.5 mean steps.
4. **"Your beacons all collide in the fast backend. Do you have any link state at all?"**
   In the timestep backend the beacons are synchronised, a known artefact we fixed in the reference backend with jitter. So the live signal comes mainly from SOS floods. Adding jitter to the timestep backend is a one-line change.
5. **"Where does σ = 11 dB enter the results?"**
   Only Fig. 2. The timestep backend uses mean path loss, so through the heavy preset every in-range link is clean, and the step at severe is where long links fall below sensitivity.
6. **"How would a node get the global state Dijkstra needs?"**
   It wouldn't, in the protocol as described. The planners are oracles, and link-state dissemination and its airtime cost are future work.
7. **"Is 7.3× your number at 10×10?"**
   No, it's 4.7× at 10×10. 7.3× is at 5×5.
8. **"Is ETSI's 1% rule even relevant in India's 865–867 MHz band?"**
   Probably not, since IN865 reportedly has no duty-cycle limit (verify this). But the airtime problem is real: at ~30 neighbours, SF12 and 30 s beacons, each receiver's channel is saturated.

---

## 16. Fixes for a journal version, ranked by impact

1. Gate each hop on the channel, with Bernoulli(link PDR) or ETX retransmissions. Report **end-to-end SOS delivery to a rescue node**, and its latency.
2. Add jitter to beacons in the timestep backend. Add shadowing, at least per link per episode. Re-run V-B and V-C.
3. Estimate PDR per link on the receiver side, using sequence numbers. Either model link-state dissemination and its airtime, or restrict the planners to local information.
4. Randomise safe-zone placement. Mask actions. Add a constant-action baseline, a random baseline and a greedy-geographic baseline. Train at least 5 seeds and evaluate all of them.
5. Add decentralised baselines: flooding, Meshtastic managed flooding, OLSR-ETX or BATMAN, and GPSR.
6. Use sparser or larger meshes and longer episodes, so that failures, battery and the PDR window actually matter. Evaluate burst failures.
7. Use paired tests, and aggregate per training seed.
8. Time both backends with the same agent, and quote the 10×10 figure.
9. Fix the duty-cycle arithmetic and the jurisdiction, specify the real on-air header, and drop the LoRaWAN MTU.

---

## Appendix A: verification scripts (`redteam/`)

| Script | What it shows | Input |
|---|---|---|
| [`per_table.py`](redteam/per_table.py) | Backend link PDR (no shadowing) vs Fig. 2's shadowed PDR at grid distances; capture margin by preset; time on air and duty cycle by frame size | re-implemented `phy.py` formulas |
| [`beacon_round.py`](redteam/beacon_round.py) | Zero beacon receptions survive a synchronised round, at every preset | re-implemented `_contention_mask` |
| [`action_geom.py`](redteam/action_geom.py) | The 8 lowest-ID slots vs the safe-zone geometry; the bottom-corner counterfactual | re-implemented topology |
| [`seed_starts.py`](redteam/seed_starts.py) | Exact evaluation start nodes (validated against the artifacts); optimal vs always-action-0 | re-implemented reset logic; needs numpy |
| [`random_policy.py`](redteam/random_policy.py) | Uniform-random, always-0 and greedy policies over uniform start nodes | re-implemented topology |
| [`pdr_dist.py`](redteam/pdr_dist.py) | Per-episode `mean_pdr_seen` distribution: bunching at 0, 0.5 and 1 | committed CSVs |
| [`speed.py`](redteam/speed.py) | Speedup per grid size | `results_rev1/scalability*.csv` |

Run them from this folder: `python redteam/<script>.py <args>`.
- `pdr_dist.py` takes CSV paths as arguments.
- `speed.py` takes the scalability CSVs.

They import nothing from `<CODE>`, and they write nothing.

## Appendix B: external sources consulted (verify before quoting)

- LoRaSim path-loss parameters: [arXiv 1704.04174](https://arxiv.org/pdf/1704.04174), [arXiv 1902.04383](https://arxiv.org/pdf/1902.04383)
- India 865–867 MHz: [DoT clarification letter (power limits)](https://dot.gov.in/sites/default/files/Clarification%20ETA%20865-867%20MHz.pdf?download=1); the claim that IN865 has no duty-cycle limit is quoted from the LoRaWAN Regional Parameters in a [Pycom forum thread](https://forum.pycom.io/post/23223); [GSR 853(E), 2021 rules](https://www.thc.nic.in/Central%20Governmental%20Rules/use%20of%20low%20power%20Equipment%20in%20the%20frequency%20band%20865%20to%20868%20MHz%20for%20Short%20Range%20Devices%20Exemption%20from%20Licence%20Rules,2021.pdf)
- Disaster deaths: [OWID, a century of disaster deaths](https://ourworldindata.org/century-disaster-deaths), [OWID decadal deaths by type](https://ourworldindata.org/grapher/decadal-deaths-disasters-type), [vLex, "Hit by Disaster"](https://international.vlex.com/vid/hit-by-disaster-41442758)
- IEEE 802.15.4a channel model final report: [15-04-0662](https://mentor.ieee.org/802.15/dcn/04/15-04-0662-02-004a-channel-model-final-report-r1.pdf); [MathWorks UWB channel model notes](https://la.mathworks.com/help/comm/ug/uwb-channel-model.html)
