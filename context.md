# ABOT: shared context for every session in this folder

Loaded into every session through `CLAUDE.md`. It covers what the paper claims, where each piece
lives in the code, which committed file backs each number, and where the traps are. If you learn
something durable, add it here; this file syncs between machines through git.

## 0. Layout and conventions

- **This folder (`pptNprep/`)** holds the presentation and conference prep for the paper. It's a git repo shared across machines.
- **The paper (canonical, camera-ready)** is `ABOT- A Decentralized LoRa Mesh Communication Framework for Post-Disaster Environments.docx`, in this folder.
- **`<CODE>`** is the code/research directory. It lives at a different path on each machine, and the SessionStart hook prints it. It means the folder that contains `darwinV2/` plus the paper drafts and audit notes. **It is read-only**: see `CLAUDE.md`. Every code path below is relative to `<CODE>`.
- **Source of truth:** the paper is what was published, the code is what actually ran, and the committed result files are what the numbers come from. When they disagree, say so; don't silently pick one. §7 lists the known disagreements.

## 1. The paper at a glance

- **Title:** *ABOT: A Decentralized LoRa Mesh Communication Framework for Post-Disaster Environments.*
- **Authors:** Aniraj Singh and Azzah Mallick, Dept. of CSE, Amity University, Uttar Pradesh, India.
- **Venue:** IEEE Region 10 Humanitarian Technology Conference (R10-HTC) 2026, Bangkok. This comes from the source folder name `bangkok- R10-HTC-2026`.
- **Submission ID:** probably `m92387`. `<CODE>/m92387-mallick paper.pdf` is the originally submitted version.
- **History:** three reviews (R1 Accept 4, R2 Borderline 3, R3 Accept 4; R1 and R3 ticked "best paper: yes"). The paper was revised; the camera-ready docx is dated 2026-08-30, and a copyright receipt sits next to the source folder.
- **One-line pitch:** a gateway-free LoRa mesh where every node is both terminal and relay. Each node derives link quality (PDR, RSSI, neighbour reachability) from the beacons it hears, and routing uses that live state continuously, not only after a failure. A vectorised simulator makes RL-scale experiments possible, and a PPO routing agent is included as an **exploratory** add-on. Everything is simulation only.
- **What the evidence supports:**
  1. **Live link state is where the gain is.** Taking live PDR out of Dijkstra's edge cost drops mean link PDR from 0.267 to 0.145: about 1.8–1.9× at intact through heavy, about 1.5× at severe/extreme. Isolating replanning on the 43 seeds where both arms plan the same first route gives 0.3098 vs 0.2067: 1.50×, p = 0.0057, r_rb = −0.346.
  2. **PPO is not better overall.** Every agent hits ~100% success. On steps, PPO beats `dijkstra_dynamic` at both grid sizes, ties the three fastest planners at 15×15, and trails them at 10×10. The paper frames this as a lower bound, because both setup asymmetries work against PPO.
  3. **Fast backend.** Up to 7.3× faster than the SimPy reference with contention on (every reported result uses contention), and up to 303× without it. KS tests: alive-node counts are equivalent (p = 0.98); PDR and delivery count are not (p < 10⁻³).
  4. **Q-value gossip makes no measurable difference,** and its merge rule isn't wired in. The ablation tests transport cost only.
  5. **Severity sweep.** Only `dijkstra_dynamic`'s PDR moves, and it drops in one step at "severe". PPO is flat apart from one seed block that livelocks.
  6. **Channel model sanity check.** The distance where PDR hits 0.5 shrinks from about 45.5 km (intact) to 637 m (extreme). This shows the model is internally consistent, not that it matches real RF.

## 2. Section-by-section cheat sheet (numbers to quote)

**I. Introduction**
- Disasters have risen since 1960, with 6.7 M deaths in the 1990s [3].
- Why LoRa: km-scale range at low power, low energy per bit, licence-free ISM band [5].
- Mesh avoids depending on any single node [6].
- Gateway bottleneck: delivery drops below 50% [1].
- The RL part is explicitly exploratory, and validation is simulation only.

**II. Related Work**
- Titan [4]: LPWAN SAR, but centralised.
- ESP32 + NEO-6M self-healing mesh [5].
- Abidde et al. [7]: AI-optimised mesh routing, not LoRa-specific.
- Power-aware routing [8].
- IoT that depends on infrastructure [11].
- Meshtastic [12], Project OWL / DuckLink [13], Disaster Radio.
- **Three gaps:**
  - no simulator with an RL interface at episode rates;
  - link-quality routing that runs on static topology or recomputes only after a failure;
  - no benchmarking across levels of infrastructure damage.

**III. Proposed System**

Fully peer-to-peer: every node is both terminal and relay. Distress messages carry GPS and travel hop by hop toward better-connected neighbours.

*Table I parameters:*

| Parameter | Value |
|---|---|
| Band | 865 MHz (India ISM, de-licensed 865–867 MHz) |
| TX power | +20 dBm |
| PL(d₀) | 31.2 dB |
| Path-loss exponent n_PL | 3.8 |
| Shadowing σ | 11 dB |
| RX sensitivity | −137 dBm |
| Spreading factor / bandwidth | SF12 / 125 kHz |
| MTU | 51 B (SF12, DR0) |

- **Path loss:** `PL(d) = 31.2 + 10·n_PL·log10(d)` plus log-normal shadowing X_σ. Grounded in IEEE 802.15.4a and post-earthquake LoRa data, and explicitly unvalidated against hardware.
- **Severity presets (n_PL, σ dB):**

  | Preset | n_PL | σ (dB) |
  |---|---|---|
  | intact | 2.7 | 7.0 |
  | moderate | 3.0 | 9.0 |
  | **heavy (default)** | 3.8 | 11.0 |
  | severe | 4.2 | 12.5 |
  | extreme | 4.5 | 14.0 |

- **Contention:** slotted ALOHA with capture. The strongest frame by mean RSSI survives only if it beats the next by ≥ 6 dB; otherwise every frame is lost [2].
- **Packets:**
  - 34-byte header: msg ID, source (previous hop), destination, origin (never changes), type, priority, hop count, TTL 16, timestamp, RSSI, payload size.
  - Message types: BEACON, SOS_ALERT (highest priority), ROUTE_UPDATE, ACK, GOSSIP.
  - Beacons go out every 30 s.
- **Forwarding:** hybrid Gossip3 (forward probability p = 0.75; suppress after hearing K = 3 duplicates) plus geo-greedy unicast.
  - Haas et al. [9] find a bimodal threshold near p ≈ 0.6–0.7, so 0.75 leaves margin.
  - It saves about 25% of the transmissions a full flood would use.
- **Gossip payload:** 42 B = a 2 B count plus 10 entries of 4 B. That fits inside the 51 B MTU; if a node has more than 10 entries it sends the top 10 by |Q|.
- **Battery and failures:**
  - Battery drains linearly over 300 s. Below 20% charge, delivery probability is scaled by b/0.20.
  - Failure modes: sudden (Poisson), graceful (battery drain), mixed (50/50, the default), and burst (everything within one grid cell of an epicentre, never gateways).
  - Failure rate λ_fail = 1/3600 s⁻¹.
- **Link-state monitoring:**
  - PDR over a 50-packet window (about 25 min at SF12 beacon rate), plus RSSI and the fraction of neighbours reachable.
  - Each node computes these locally from the beacons it hears; a beacon carries only the sender's ID.
  - A 256-entry seen-cache filters duplicates.
- **Routing:** dynamic Dijkstra recomputed on live state.
- **PPO observation (24 values):** 9 base features (x, y, local PDR, reachable count, battery, distance to nearest safe zone, cos/sin of the bearing to it, elapsed fraction), 8 neighbour PDRs, and 7 extras (unit vector to the nearest alive gateway, hop count to it, local density, PDR trend, minimum neighbour PDR, maximum neighbour RSSI).
- **Two asymmetries, both against PPO:**
  - the planners see a global snapshot of the network, while PPO sees only its local observation;
  - the planners can choose any neighbour, while PPO picks from a fixed 8-slot list.
- **RL environment:**
  - Gymnasium; one step = 10 s. SOS traffic every 10 steps, gossip every 5, beacons every 3.
  - Two safe zones; episodes cap at 200 steps (2,000 s, about 33 min).
- **PPO training:**
  - SB3 defaults: MLP with 2×64 tanh units, γ 0.99, λ_GAE 0.95, entropy coefficient 0.01, learning rate 3e-4, clip 0.2, batch 64, 10 epochs.
  - 7 in-process environments × 200 steps = 1,400 transitions per update.
  - 3 seeds × 200k steps (summed across the 7 workers), on CPU.
- **Reward:**

  | Event | Reward |
  |---|---|
  | Reach a safe zone | +100 |
  | Each step | −1 |
  | Zero reachable neighbours | −20 |
  | Dead or missing neighbour chosen | −20 |
  | New SOS delivered | +5 |
  | Link quality | −0.5·(1 − PDR) |

- **Action space:** Discrete(8), indexing the neighbour list sorted by ID. Node degree is 30.7 on average at 10×10 (400 m spacing, 1500 m range) and up to 44.

**IV. Simulation Backend**
- The SimPy reference was too slow for RL, so it was replaced by a timestep backend. Both share the same protocol, channel, contention and failure models.
- **Contention is resolved differently:** the reference applies capture over true continuous-time overlap of 2.47 s SF12 frames, while the timestep backend does it once per propagation round. That makes the reference the harsher of the two.
- **Speedup:** 7.3× with contention, 303× without. Sweeping λ_fail over {0, 1/3600, 1/1800} doesn't change it.
- **KS tests (20 seeds):** alive-node counts match (p = 0.98); PDR and delivery count don't (p < 10⁻³).

**IV-A. Q-value gossip**
- Gossip carries the critic's V(s), which the code calls a "Q-table".
- Encoding: uint16 index plus uint16 quantised value per entry, flooded with TTL 4.
- The merge rule `Q_new = (1−α)·Q_local + α·Q_recv` with α = 0.3 is implemented but **not connected to the receive path**.
- `GossipCallback` averages value estimates across workers.
- **Ablation:** 3 seeds × 300 episodes per arm.

  | Metric | Gossip on | Gossip off | p |
  |---|---|---|---|
  | Success | 1.000 | 1.000 | — |
  | Steps to safe zone | 2.487 | 2.497 | 0.842 |
  | Reward | 101.42 | 101.27 | 0.826 |

  This shows the pipeline doesn't depend on gossip. It doesn't show gossip helps.

**V. Experimental Results** (10×10 = 100 nodes; scalability up to 30×30 = 900)

*Baselines:*
- `dijkstra_static` and `astar_static` use hop count (A* with a Euclidean heuristic).
- `dijkstra_dynamic` and `astar_dynamic` use PDR-weighted edges and replan if a planned hop dies, or its PDR falls below 0.5, within the next 3 hops.

*Primary metric:* reward is almost a monotone function of path length (Pearson r −0.987 to −0.993), so steps-to-safe-zone is the primary metric. Results are reported as median [IQR].

**V-A. Baseline comparison** (heavy severity, 100 episodes per agent per grid)

| | 10×10 median [IQR] | 10×10 mean | 15×15 median [IQR] | 15×15 mean |
|---|---|---|---|---|
| PPO | 3 [2, 3] | 2.48 | 4 [3, 4.25] | 3.56 |
| Three fastest planners | 2 [2, 3] | 2.17 | 3 [2, 4] | 3.23–3.25 |
| dijkstra_dynamic | 3 [2, 4] | 3.23 | 4 [3, 6] | 4.40 |

*Table II* (Mann–Whitney U, Holm-corrected; negative r_rb favours PPO):

| Grid | Baseline | r_rb | p_corr | Verdict |
|---|---|---|---|---|
| 10×10 | dijkstra_dynamic | −0.358 | 2.5×10⁻⁵ | PPO better |
| 10×10 | astar_dynamic / astar_static / dijkstra_static | +0.184 | 0.047 | PPO worse |
| 15×15 | dijkstra_dynamic | −0.281 | 1.9×10⁻³ | PPO better |
| 15×15 | the other three | +0.137 to +0.138 | 0.255 | no difference |

**V-B. Severity sweep** (250 episodes per agent per preset = 5 seeds × 50)
- `dijkstra_dynamic` PDR is about 0.28 from intact to heavy, then 0.218 (severe) and 0.216 (extreme): a 23% step down.
- Every other agent moves by less than 0.02.
- PPO reward is 101.4–102.2 in 4 of the 5 seed blocks. Its success is 0.996 at every preset (classical planners: 1.000).
- **The outlier is the fourth seed block (seed 3):** about 16.9 reward from intact to heavy and about 22.9 at severe/extreme. That pulls the sweep means to 84.6 / 86.0, while the median stays 101.5.
- **Cause: livelock.** The deterministic policy keeps choosing action 0, whose neighbour is dead. Each attempt is rejected with −20 and the next observation looks almost the same. Neither the isolation penalty nor the gateway check breaks the loop.

**V-C. Communication-aware ablation**
- Static and dynamic arms run on the same backend and the same 100 seeds. The paper's "steps-to-safe-zone are identical on all 100" is a fidelity check: the static planners re-run on the timestep backend take exactly the same steps as in their archived SimPy runs (`results_commaware/FINDINGS.md` §1). It does **not** mean static and dynamic take equal steps; they don't (2.17 vs 3.23).
- Mean link PDR is 0.267 (dynamic) vs 0.145 (static). Across presets the ratio is about 1.8–1.9× at intact through heavy and about 1.5× at severe/extreme.
- When matched on steps, the ratio widens to 1.9–2.6×.
- **Hash-seed caveat:** across 8 seeds, `dijkstra_dynamic` PDR ranges 0.264–0.294. The separation is robust; the third significant figure isn't.
- **The A\* pair is uninformative:** its replan trigger fires in only 3 of 100 episodes, giving 1.03× (p = 0.886).
- **The cleanest number:** the Dijkstra pair on the 43 seeds where both arms plan the same first route: 0.2067 vs 0.3098, 1.50×.

**V-D. Channel validation (Fig. 2)**

| Preset | Distance where PDR = 0.5 | PDR at 1500 m |
|---|---|---|
| intact | 45.5 km | 1.000 |
| moderate | 15.5 km | 0.999 |
| heavy | 2.0 km | 0.664 |
| severe | 1.03 km | 0.286 |
| extreme | 637 m | 0.109 |

At 400 m (the grid spacing) PDR stays above 0.73 under every preset.

**VI. Limitations and Future Work**
1. Simulation only, at up to 900 nodes.
2. Duty cycle: 30 s beacons at SF12 use about 4.4% of airtime, against the 1% limit in ETSI EN 300 220-2.
3. Action-space truncation (8 slots vs a mean degree of 30.7) causes the livelock.
4. The critic didn't converge: final explained variance −0.67, 0.18 and 0.71 across the three seeds.
5. Adoption risk.

*Future work:* firmware for Meshtastic-compatible boards (T-Beam, Heltec, RAK); pre-positioned mains or solar relays; a phased rollout (responders, then fixed relays, then the public).

**VII. Conclusion.** Restates the above; the next steps are hardware validation and SAR integration.

**Figures**
- **Fig. 1** is the four-layer architecture, from `darwinV2/results_rev2/figures/fig1_architecture_v2.png`. The layers, bottom to top: Physical (LoRa), MAC and Forwarding (ABOT-Comm), Link-State Monitoring, Routing and Evacuation. A dashed `DisasterEvacEnv` box wraps them as the simulation harness.
- **Fig. 2** is PDR vs distance, from `darwinV2/results_rev2/figures/fig4_pdr_vs_distance.png`.
- In the docx they are `word/media/image1.png` and `image2.png`. The docx equations are OMML, so python-docx `paragraph.text` drops them; read the `m:t` text out of `word/document.xml` instead.

## 3. Name map (paper ↔ code)

| Paper | Code |
|---|---|
| ABOT | **DARWIN** (repo/package name, "Disaster-Aware Routing With Intelligent mesh Nodes") |
| ABOT-Comm | DARWIN-Comm (`src/comm/`, `src/sim/`) |
| "Q-table", Q-value gossip | the PPO critic's V(s) per node (`GossipCallback`) |
| timestep backend | `TimeSteppedMeshStateProvider` (`src/sim/timestep.py`) |
| SimPy / reference backend | `SimPyMeshStateProvider` + `MeshNetwork` + `MeshNode` |
| safe zone / rescue node | gateway node (corner nodes from `assign_safe_zones`) |
| RL environment | `DisasterEvacEnv` (the code descends from an "evacuation router"; the naming is legacy) |
| dijkstra_static / astar_static | `DijkstraBaseline` / `AStarBaseline` |
| dijkstra_dynamic / astar_dynamic | `DynamicDijkstraBaseline` / `DynamicAStarBaseline` |
| (not in the paper) | `CommAwareDijkstraBaseline`: legacy, ignore |
| "fourth seed block" | `seed == 3` (0-indexed) |

## 4. Code map: where each concept lives

Paths are relative to `<CODE>/darwinV2/`. Line numbers were checked on 2026-10-07.

| Concept | Location |
|---|---|
| All tunable constants (beacon 30 s, PDR window 50, seen-cache 256, gossip entries 10, n_PL 3.8, σ 11, p 0.75, K 3, drain 300 s, contention on, capture 6 dB) | `src/config.py:24-98` (`SimConfig`) |
| Training config (7 envs, 200k steps, 200-step episodes, 10 s/step) | `src/config.py:102-132` |
| Severity presets | `src/config.py:142-148` (`DAMAGE_SEVERITY`) |
| SF12 / 125 kHz / 865 MHz / 51 B MTU / +20 dBm | `src/comm/phy.py:14-22` |
| Sensitivity −137 dBm (noise floor + −20 dB SNR) | `src/comm/phy.py:24-36` |
| Time on air (Semtech AN1200.13) | `src/comm/phy.py:54` (`time_on_air(51)` ≈ 2.47 s; `time_on_air(20)` ≈ 1.32 s) |
| Log-distance path loss | `src/comm/phy.py:91` (`disaster_path_loss`); old COST-231 at `:134` is deprecated |
| PER curve (logistic, k = 1.5, centred on −20 dB SNR) | `src/comm/phy.py:199` |
| Duty-cycle helper (**not enforced**) | `src/comm/phy.py:247` |
| Shadowing / RSSI / per-link PER; per-preset channel | `src/comm/channel.py:28, 50` (`LoRaChannel`), `:78` (`from_severity`) |
| Packet: priorities, 5 message types, 34 B header | `src/comm/packet.py:30, 37, 63-64` |
| Grid topology, 1500 m range, corner safe zones | `src/sim/topology.py:20, 60, 108` |
| Failure modes (sudden/graceful/burst/mixed) | `src/sim/failure.py:23, 125, 131, 150, 196` (SimPy); `src/sim/timestep.py:239-314` (timestep) |
| SimPy node: contention and capture, beacon jitter, Gossip3, suppression, battery scaling | `src/sim/node.py:82` (`ContentionTracker`), `:260-278`, `:361` (`_should_forward`), `:388` (`_deferred_broadcast`), `:513` |
| Timestep backend | `src/sim/timestep.py:54` (class), `:427` (`advance`), `:452` (beacons; payload is the node ID only, `:463`), `:476` (`_propagate_all`, vectorised Bernoulli `:515`), `:592` (`_contention_mask`), `:673` (`_geo_greedy`), `:711` (mesh-state snapshot) |
| Backend interface | `src/nav/mesh_provider.py:47` (`MeshStateProvider`), `:103` (SimPy wrapper), `:224` (test stub) |
| RL env | `src/nav/env.py:36` (class), `:84-103` (defaults: 5×5, mixed failures, timestep backend), `:241` (`reset`), `:297` (`step`) |
| Reward terms | `src/nav/env.py:302` (−1), `:311-315` (invalid action −20), `:332-333` (isolation −20), `:336-337` (+5), `:340-341` (PDR term), `:343-346` (+100) |
| SOS every 10 steps, gossip every 5 | `src/nav/env.py:318, 322` |
| Action indexing (dead neighbours kept in the ID-sorted list) | `src/nav/env.py:380-388`; `strict_action_space` explained at `:64-79` |
| 24-dim observation | `src/nav/state.py:7-32` (layout), `:63` (`build_observation`), `:134-138` (neighbour PDR slots), `:140-186` (the 7 extras) |
| Gossip codec, 42 B check, merge, injection (TTL 4) | `src/nav/gossip.py:37-42, 46, 90, 127, 194` |
| **Merge not wired** | `src/nav/gossip.py:211-222` (`absorb_incoming_gossip` is a stub); `merge_q_tables` has no callers |
| PPO hyperparameters, `GossipCallback`, `train_ppo` | `src/train/ppo_trainer.py:52-62, 80, 170, 257` |
| Training script used for the paper (DummyVecEnv, 7 envs) | `scripts/train_v2_main.py:48-64, 125-127` |
| Episode runner (planners get the **global** snapshot) | `src/train/runner.py:33, 95` |
| Baselines | `src/train/baselines.py:23` (Dijkstra), `:175` (A\*), `:251` (DynamicDijkstra: replan check `:312`, edge weight 1/max(PDR, 0.01) `:342`, hash-order set iteration `:330-336`), `:359` (DynamicA\*) |
| Statistics (bootstrap CI, Holm, Mann–Whitney + rank-biserial) | `src/eval/stats.py:47, 75, 120` |
| Experiment runners | `src/eval/experiments.py:68` (baseline factory), `:91` (Monte Carlo), `:176`, `:262` |
| Dashboard (Streamlit, not used in the paper) | `src/viz/dashboard.py` |
| Tests (20 files, ~346 test functions; not run in this folder) | `tests/` |

## 5. Evidence map: paper number → file → producing script

Paths are relative to `<CODE>/darwinV2/`. `results_rev1/` is the archived run. `results_rev2/` re-analyses the same data without re-simulating. `results_commaware/` and `results_15x15/` are the single-backend re-runs of the static planners.

| Paper claim | Where the number lives | Produced by |
|---|---|---|
| Table I constants, 34 B header, 42 B gossip | `src/comm/phy.py`, `src/config.py`, `src/comm/packet.py`, `src/nav/gossip.py` | — |
| Mean degree 30.7, max 44 | `results_rev2/action_space_audit.json` | `scripts/rebuild_stats_rev2.py` |
| 7.3× (5×5, contention on) | `results_rev1/scalability.csv`, `results_rev1/logs/scalability.log` | `scripts/benchmark_scalability.py` |
| 303× (15×15, contention off) | `results_rev1/scalability_nocontention.csv`; `results_rev1/logs/scalability_nocontention.log:92` | same |
| KS p = 0.98 / p < 10⁻³ | `results_rev1/equivalence/ks_table.csv` | `benchmarks/run_backend_equivalence.py` |
| Gossip ablation | `results_rev1/gossip_ablation/gossip_ablation_summary.json` (+ `.csv`, `.png`) | `scripts/run_gossip_ablation.py` |
| Trained models | `results_rev1/ppo_10x10_seed{0,1,2}[_nogossip].zip`, `checkpoints_seed*/`, `tb/seed_*/progress.csv`, `training_summary*.json` | `scripts/train_v2_main.py` |
| Explained variance −0.67 / 0.18 / 0.71 | `results_rev1/convergence_summary.json` | training logs |
| 10×10 medians and Table II rows | `results_rev1/baselines.csv` (PPO and dynamic planners), `results_commaware/commaware_main_10x10.csv` (static planners); stats in `results_rev2/table_v.md`, `results_rev2/baselines_summary.json` | `scripts/run_monte_carlo.py`, `results_commaware/run_commaware.py`, `scripts/rebuild_stats_rev2.py` |
| 15×15 rows (all 5 agents, Holm over 4 tests) | `results_15x15/statics_15x15.csv`, `impact_15x15.json`, `FINDINGS.md` | `results_15x15/run_15x15.py`, `analyze_15x15.py` |
| Pearson r −0.987 to −0.993 | computed from `results_rev1/baselines.csv` (`<CODE>/AUDIT-RERUN.md` §3, check A4) | — |
| Severity sweep | `results_rev1/damage_severity.csv` (per-seed), `damage_severity_summary.json`; `results_rev2/damage_severity_summary.json`; static arms in `results_commaware/commaware_severity_episodes.csv` | `scripts/run_damage_severity.py` |
| Seed-3 outlier | `results_rev2/seed3_outlier.json` (it says the "−4131" figure is a reconstruction and **not citable**) | `scripts/rebuild_stats_rev2.py` |
| Comm-aware ratios 0.267 vs 0.145 | `results_commaware/FINDINGS.md`, `impact_report.json` | `results_commaware/analyze_impact.py` |
| 43-seed 0.2067 vs 0.3098; A\* 1.03× | `results_commaware/conditional_vc.json`, `pair_mechanism.json` | `conditional_vc.py`, `diagnose_pairs.py` |
| Hash-seed range 0.264–0.294 | `results_commaware/reproducibility_note.json` | — |
| Fig. 2 crossings and PDR at 1500 m | `results_rev2/figures/fig4_pdr_vs_distance.csv` | `scripts/make_fig4_pdr_distance.py` |
| Fig. 1 | `results_rev2/figures/fig1_architecture_v2.{png,pdf}` | `scripts/make_fig1_architecture_v2.py` |

`<CODE>/AUDIT-RERUN.md` §3 has a read-only script that re-derives most of these from the artifacts, and §7 lists claims that must **not** reappear. Treat it as the fact-check list.

## 6. Material for slides

- **Figures, 300 dpi PNG plus vector PDF**, in `<CODE>/darwinV2/results_rev2/figures/`:
  - `fig1_architecture_v2` (paper Fig. 1), and `fig1_architecture` (a three-layer variant)
  - `fig4_pdr_vs_distance` (paper Fig. 2)
  - `fig_baselines` (baseline comparison, single-backend rebuild)
  - `damage_severity` (severity sweep, single-backend rebuild)
  - `fig_learning_curve`
  - `fig_scalability`
  - also `results_rev1/gossip_ablation/gossip_ablation.png`
- **Avoid** these older or mixed-backend versions: `results_rev2/figures/archive_mixed_backend/`, `darwinV2/figures/`, and `results_rev1/figures/`.
- **Tables cut from the paper for length**, usable as backup slides: `results_rev2/tables/` (notation, PPO config, speedup, significance, KS, gossip, contributions) and `results_rev2/table_v.md`. Their wording predates the audit; for example `table_ix_contributions.md` says "identical inputs" and "three-layer". Re-check every cell against §1–§2 before using one.
- To use a code-dir figure, **copy it into this folder** (`assets/` or similar). Copying out is allowed.

## 7. Discrepancies and traps

- **`darwinV2/README.md` is out of date** (it predates v2). It says SF9, COST-231 with σ = 8 dB, a 17-value observation, a 32-byte header, 115 B payloads, 145 tests, and an observation without the 7 extras. The truth is SF12, log-distance path loss, 24 values, 34 B, 51 B MTU, and 20 test files.
- **Inconsistencies inside the paper itself:**
  - The text says "three functional layers", but the Fig. 1 caption says "Four Layer"; v2 of the figure splits MAC/forwarding into its own layer.
  - The path-loss sentence cites "IEEE 802.15.4a CM6", but the code comments cite CM4 (n = 3.5, σ = 11) plus Ferreira et al. 2020 (n ≈ 3.8–4.2).
  - The text says "Al-Hadhrami et al. [8]", but reference [8] is Olajide (PARA, PLoS ONE 2018).
  - [11] is a deep-RL LoRa transmission-policy paper, yet it is cited for IoT situational awareness and for the simulator gap.
  - The keywords line has a stray ", ,".
  - The abstract says results highlight "limitations of RL-based routing under extreme network collapse conditions". The body (V-B) doesn't support a severity-specific weakness: PPO is flat across presets, and the seed-3 livelock appears at every preset (≈16.9 intact–heavy, ≈22.9 severe/extreme). On stage: the weakness comes from the 8-slot action space, not from severity.
  - V-C's "steps-to-safe-zone are identical on all 100" reads as if the static and dynamic arms take identical steps, which contradicts "3.23 against 2.17 steps" two sentences later. It refers to the backend re-run fidelity check (see §2 V-C). A technical listener may catch this.
- **The +5 SOS reward:** the paper says "+5 per new SOS delivered". The code gives +5 at most once per step if *any* new delivery happened (`env.py:336-337`).
- **Observation slots and actions don't line up.** Neighbour-PDR slots are filled from the *alive* neighbours sorted by ID, as the simulator reports them; nothing is taken from beacons actually heard (`state.py:134-138`; see §19). Actions index the *full* ID-sorted list, dead nodes included (`env.py:304-315`). Once neighbours die, slot i and action i can be different nodes. This is the "addressable but unobservable" problem behind the livelock.
- **Planners aren't limited to 8 slots:** `strict_action_space=False` (`env.py:311`) lets them pick any neighbour index, while PPO can only emit 0–7.
- **Which PPO model was evaluated:** the Monte Carlo and severity runs use only the seed-0 checkpoint (`results_rev1/ppo_10x10_seed0.zip`). The 3 seeds appear in training, convergence and the gossip ablation (3 per arm).
- **The mixed-backend history:** `scripts/run_monte_carlo.py` originally ran the static planners on SimPy and everything else on the timestep backend. That confounded the early static-vs-dynamic numbers (archived ratios of 4.71× and 3.36×). The paper uses the single-backend re-runs in `results_commaware/` and `results_15x15/`. Don't quote the archived ratios.
- **Episodes are tiny:** 2–4 hops, because a 1500 m range on 400 m spacing gives about 30 neighbours per node. Every agent hits ~100% success, so agents are compared on path efficiency. Expect "isn't the task too easy?"
- **Duty cycle** isn't enforced anywhere in the simulation (`phy.py:247`).
- **Which draft is which** (all in `<CODE>`, oldest first):
  1. `paper.md` (90 KB, longest)
  2. `selected-paper.md`
  3. `paper-rev2.md`
  4. `curr-draft.md` (audited 2026-08-27)
  5. `curr-draft-rev.md` (+ `.bak`–`.bak9`)
  6. `final-ish*.md`
  7. `FINAL.md` (closest text to the camera-ready)
  8. `ABOT-conference-paper.docx` (an earlier docx)
  9. the camera-ready docx in **this** folder

  Process docs: `REVISION-WORKORDER.md`, `AUDIT-RERUN.md`, `RUN-15x15-STATICS.md`, `SECTION-V-PROVENANCE.md`, `CHANGES-final-ish.md`, `darwinV2/PAPER_REVISIONS.md`. **Quote only the camera-ready paper**; earlier drafts contain claims that were removed for being wrong.

## 8. Reviewer comments (`<CODE>/Review.txt`) and where the paper answers them

| Reviewer ask | Answered in |
|---|---|
| R1: say clearly that it's simulation only | Abstract, I, VI, VII |
| R1: cite disaster statistics; explain why LoRa | I ([3]; ¶2) |
| R1: reward balancing; convergence | III RL-env reward paragraph; VI (explained variance) |
| R1: gossip ablation | IV-A (null result, unwired merge disclosed) |
| R1: hedge the PPO weaknesses | "exploratory", "lower bound" framing in I and V-A |
| R1: speedup under failures | IV (λ_fail sweep) |
| R1: deployment | VI Future Work |
| R1: why 42 B; why p = 0.75 | III (gossip payload budget; Haas bimodality) |
| R1: captions, grammar, notation table | captions improved; notation table cut for length (`results_rev2/tables/table_notation.md`) |
| R2: no contention model | slotted ALOHA + 6 dB capture added to both backends |
| R2: soften "faithfully captures" | V-D says "internal consistency only" |
| R2: speedup is against one specific tool | IV says the reference is one implementation, not DES in general |
| R2: show the backends are equivalent | KS tests in IV |
| R2: frame the ML as exploratory | I and V-A |
| R2: summary table, statistics, missing "Table V", citations | Table II with Holm-corrected tests. The summary table was drafted (`table_ix_contributions.md`) but cut. |
| R3: redraw Fig. 1 as clean layers | `fig1_architecture_v2` |
| R3: expand the gossip section | IV-A |
| R3: abbreviations at first use | done in text |
| R3: qualify the "first time" claim | the claim was removed |
| R3: refer to tables and figures in the text | done |

R2's core worry is the one the audience will share: **does the simulator capture real wireless behaviour?**

**What the reviewers actually saw** (checked 2026-10-13 against the submitted PDF, `m92387-mallick paper.pdf`):
- The submission also reported only a "PDR" score and steps, never SOS arrival at a rescuer or delay. Its V-A had the static planners at PDR ≈ 0.64 and the dynamic ones at 1.0 (intact and moderate). Its conclusion said live PDR-weighted routing "improves packet delivery" and that the simulator "faithfully captures" failure dynamics.
- R2's "very high delivery rates" most likely refers to those PDR = 1.0 figures. No reviewer asked for end-to-end delivery or latency (red-team P-01).
- The camera-ready abstract's results sentence is word-for-word the submission's, so it still describes the old numbers (P-08). The revision dropped "faithfully captures", "first time" and the 242× claim, but kept the delivery wording in the abstract and conclusion.

## 9. Likely questions and grounded answers

1. **"PPO doesn't beat Dijkstra, so why use RL?"**
   - It's exploratory. The contribution is the training substrate plus an honest baseline.
   - PPO beats the comm-aware `dijkstra_dynamic` at both scales, ties the fastest planners at 15×15, and trails them at 10×10.
   - Both asymmetries handicap PPO: local vs global view, and 8 slots vs the full neighbour list.
2. **"So what is the contribution?"**
   - A gateway-free design, with link state measured continuously from beacons.
   - Evidence that live link state carries the delivery gain: about 1.8× higher mean link PDR, and 1.50× on the cleanest replanning-only subset.
   - A fast backend that makes RL experiments feasible.
   - Results scoped honestly (simulation only, with stated limits).
3. **"How realistic is the channel?"**
   - Log-distance path loss with shadowing, slotted ALOHA with 6 dB capture, and five damage presets.
   - Validated for internal consistency only, not against measured RF.
   - The KS tests show the two backends disagree on PDR under contention.
4. **"Why 865 MHz and SF12?"** 865–867 MHz is de-licensed in India. SF12 gives the most range: −137 dBm sensitivity, multi-km reach without line of sight.
5. **"Is it duty-cycle legal?"** Not yet: about 4.4% vs the 1% ETSI limit. A compliant beacon schedule would shift every beacon-dependent figure. This is a stated limitation.
6. **"Why doesn't gossip help?"** The merge rule isn't connected, so only transport is exercised, and both arms already solve the 10×10 task. The null result says the pipeline doesn't depend on gossip; nothing more.
7. **"Why only 2–4 hops?"** The radio range is 1500 m on a 400 m grid (about 30 neighbours), on a 10×10 grid about 3.6 km across. That's why success is at ceiling and efficiency is the metric. Larger or sparser meshes are future work.
8. **"What's the livelock?"** In seed 3, the deterministic policy keeps picking slot 0, whose neighbour is dead. Fixed-width indexing keeps dead neighbours addressable. The fix is action masking or a variable-size neighbour set.
9. **"7.3× compared to what?"** Compared with the authors' own SimPy reference, not ns-3 or OMNeT++. It's 7.3× with contention, and 303× without it at 15×15. SimPy times out at 20×20 and above.
10. **"How do messages travel without gateways?"**
    - Beacons every 30 s build each node's link-state view.
    - SOS messages (highest priority, TTL 16) spread by Gossip3 (p = 0.75, K = 3) plus geo-greedy unicast.
    - Duplicate suppression: a 256-entry seen-cache.
11. **"Deployment path?"**
    - Firmware for Meshtastic-class boards (T-Beam, Heltec, RAK) — no new hardware.
    - Pre-positioned relays.
    - Phased rollout: responders, then fixed relays, then the public.
    - Adoption is the main risk.
12. **"Why p = 0.75 and K = 3?"** Haas et al.: gossip delivery is bimodal, with a threshold near p ≈ 0.6–0.7. 0.75 leaves margin for sparser post-disaster meshes and still saves about 25% of flood transmissions.
13. **"How were the statistics done?"**
    - Mann–Whitney U with Holm–Bonferroni correction and rank-biserial effect sizes; bootstrap CIs (`src/eval/stats.py`).
    - Medians and IQR, because reward is almost a monotone function of steps.
14. **"Can the results be reproduced?"**
    - Code and every artifact are committed, and the audit script re-derives the numbers.
    - Caveat: `dijkstra_dynamic` breaks ties by Python's hash seed, so its PDR ranges 0.264–0.294.

## 10. Working notes

- **Reading the docx:** python-docx was available on the machine where this file was written; the equations need the XML route (§2, Figures). `pypdf` and `pymupdf` were also present. **`python-pptx` was not installed** there; check before relying on it.
- **Python versions:** the code was run under Python 3.13 (README). The prep machine has 3.14.
- **Never re-run experiments or scripts in `<CODE>`.** Every number already lives in a committed artifact (§5).
- **The presenter describes themselves as non-technical.** Explain in plain English and skip code-level detail; the audience can't see the codebase either. Prep started 2026-10-12 with about a week to go. They asked for study material to cover technical concepts only (no storytelling, rehearsal or Q&A drills). The study plan is `study/abot-study-route.html`: a 14-concept prerequisite map over 7 days, with worked examples (the path-loss formula + Table I reproduces Fig. 2's crossings and 1500 m PDRs to within a few percent; grid geometry gives degree 44 max / 30.7 mean).
- **Read-only guard:** `.claude/hooks/guard.py` (pre-tool hook) plus `.claude/pyguard/` (blocks Python writes at runtime).
  - Per-machine setup: `python .claude/hooks/setup_machine.py "<code dir>"`.
  - Side effect: Python started from these sessions can't write into `<CODE>` or into any `darwinV2/` directory. That's intended.

## 11. Red-team findings (2026-10-12)

The full critique is `ABOT-red-team.md`, and its verification scripts are in `redteam/`. `ABOT-red-team.xlsx` has the same points in two tabs: attacks that need code access (30) and attacks anyone can make from the paper alone (52). Each has a Critical/Major/Minor label and a 1–100 rating of how hard it is to justify (1 = easy, 100 = hardest). They re-implement the code's formulas and read only committed CSVs. These findings were checked against the code and change how several §9 answers should be given:

- **Hops aren't gated by the channel.** The agent moves whenever the target neighbour is alive (`env.py:311-313`), so success is at ceiling at every severity by construction.
- **"Mean link PDR" (`mean_pdr_seen`) is a node-level score**, not the PDR of the links used. It averages a node's ~30 outgoing links, and a link that has never been used counts as 1.0 (`timestep.py:728-733`). `dijkstra_dynamic` uses that same score as its edge cost (`baselines.py:339-342`), so the 0.267 vs 0.145 result is partly circular.
- **No SOS-to-rescuer measure exists anywhere** (red-team P-01; checked 2026-10-12). The per-episode result files hold only success, steps, reward and `mean_pdr_seen`. Nothing in the code checks whether an SOS reached a gateway, and no latency is reported.
  - `network_pdr` (the KS "PDR") counts a message as soon as any one other node hears it (`timestep.py:382`).
  - `delivery_count` (the KS "delivery count", and the +5 trigger) counts first receptions of any packet by any node, beacons included (`timestep.py:404-419, 571`).
  - So an end-to-end SOS delivery figure can't be taken from existing data. It needs new runs, which can't be done from this folder.
- **The timestep backend has no shadowing.** Its PER cache uses mean path loss (`timestep.py:157-169`), so every in-range link has PDR ≥ 0.9998 from intact through heavy. **Fig. 2 was not made with the timestep backend:** the script queries the analytic channel (`scripts/make_fig4_pdr_distance.py:15`).
- **Every beacon collides in the timestep backend.** All beacons go out in the same round and the four nearest neighbours tie at 400 m, so 0 of 3,068 receptions survive (`redteam/beacon_round.py`). The SimPy node's docstring (`node.py:263-273`) calls this an artefact; it was fixed there with jitter, but not in the timestep backend.
- **A constant "always action 0" policy matches PPO's medians**: 3 [2, 3] at 10×10 and 4 [4, 5] at 15×15, with means of 2.71 and 4.07 against PPO's 2.48 and 3.56. It also beats `dijkstra_dynamic` on the evaluation seeds (`redteam/seed_starts.py`).
  - The reason: action slots are the 8 lowest-ID neighbours, and both safe zones (N000, N009) are in row 0.
  - The 8 slots always contain an optimal next hop, so the "8 slots handicap PPO" argument doesn't hold.
- **Gossip ablation:** at evaluation, neither arm sends any gossip packet, because the value table is empty (`gossip.py:200`, `env.py:280-288`).
- **Speedup:** it is 4.7× at 10×10; 7.3× is the 5×5 figure. The two backends were also timed with different agents (`benchmark_scalability.py:104` vs `:185`).
  - SimPy with contention ran fine up to 30×30. Only the no-contention runs timed out at 20×20 and above.
- **Time scales:** episodes last 10–30 s simulated. 60% of the fastest planners' episodes finish before the first beacon round, and battery scaling never triggers.
- **§9 answers to revisit in light of the above:**
  - Q1: the asymmetry argument.
  - Q2: "carries the delivery gain".
  - Q3: "with shadowing".
  - Q5: 4.4% assumes a 20 B frame, and the ETSI limit is a European rule, not the one for India's band.
  - Q7: routes are 1–3 hops, not 2–4.
  - Q9: the speedup at 10×10, and the timeout statement.
  - Q10: in the evaluated backend, beacons don't build anything.
- **External facts used by the critique are marked [ext]; verify them before quoting:**
  - India's IN865 band has no duty-cycle limit;
  - 1990s disaster deaths were under ~0.8 M, so the paper's "6.7 M" is likely misquoted. [3] itself has since been checked: it contains no such figure (§12);
  - LoRaSim's urban path-loss model;
  - 802.15.4a's CM numbering.

## 12. Red-team triage for the talk (2026-10-13)

`ABOT-red-team-triage.md` sorts all 82 red-team points by what they mean for the R10-HTC talk:
- **47 to ignore.**
- **25 that only constrain wording**, reduced to 13 "don't say / say instead" rules.
- **10 that could come up in Q&A**, reduced to 8 one-line answers. For the talk, these replace the §9 answers that §11 flags.

Durable facts behind it:
- **The paper links no code.** It has no repository link or availability statement, so the 30 code-access points can't be raised from the audience. They matter only as limits on what to claim.
- **[3] doesn't contain "6.7 million deaths in the 1990s".** The full text of IMF WP/12/245 (32 pp.) was searched on 2026-10-13; it gives no 1990s death toll at all. What it does say:
  - yearly disaster damage rose from about US$20 billion in the 1990s to about US$100 billion in 2000–10 (p. 5 of the PDF);
  - 97% of disaster deaths since the 1960s were in developing countries (p. 7).

  Keep 6.7 M off the slides.
- **Speedup, recomputed from `results_rev1/scalability.csv`** (contention on): 7.2× at 5×5, 4.7× at 10×10, 4.0× at 15×15, and 3.5–4.5× from 20×20 to 30×30. The paper's 7.3× is the 5×5 run at λ_fail = 0 (`results_rev1/logs/scalability.log:91`).
- **Tooling on the prep machine:**
  - The Read tool can't render PDFs (no `pdftoppm`).
  - `openpyxl`, `pypdf` and `pymupdf` sit in user site-packages, which `python -I` hides. Use `python -E -P` to keep the module-path protection and still find them.

## 13. Plain-English guide to the 52 paper-only points (2026-10-13)

`ABOT-red-team-explained.md` takes each P-point in turn: what it is, why it's an issue (every sub-problem numbered, with a matching reason), and what it means for the talk. It is grouped by the §12 triage and adds an at-a-glance table, a slide checklist and a glossary. Facts checked against the camera-ready text while writing it:
- **The paper never names its statistical tests.** It says "pairwise testing" and "rank-based tests" and reports r_rb and p_corr. "Mann–Whitney", "Holm" and "Wilcoxon" appear nowhere in the docx. Red-team rows P-34 ("Mann-Whitney U, Holm-corrected") and P-26 ("Holm family") describe the code, not the paper. If asked which test: Mann–Whitney U with Holm correction (`src/eval/stats.py`).
- **"The cleanest number" is not the paper's phrase.** It is §2's own label for the 43-seed result; P-29's row quotes it as paper wording. The paper says the subset "isolates replanning".
- **Exact paper wording behind three slide rules:**
  - "multi-kilometre range over rubble-strewn, non-line-of-sight terrain without repeaters" (III);
  - "(2,000 simulated s, roughly 33 min), a representative post-disaster routing window" (III, RL environment);
  - "roughly 4.4% channel occupancy at SF12, well above the 1% limit ETSI EN 300 220-2 sets for this band" (VI).
- **Don't gloss the results' "mean link PDR" as "the share of messages that get through".** That reading fits Fig. 2's PDR and the protocol's described link PDR. The results' figure is a node-level link-quality score (§11).
- **PPO and severity:** the paper says PPO's reward is "flat rather than degrading", and the seed-3 block rises from ≈16.9 to ≈22.9. "Doesn't get worse with damage" is accurate; "flat across all five levels" overstates it for that block.
- **Triage rule 4, refined:** "PPO matches the classical planners" overstates 10×10, where PPO is worse (p_corr 0.047). The guide now says "in the same range as the classical planners, but not better than the fastest ones: slightly behind them at 10×10, no significant difference at 15×15". The words "than the fastest ones" were added on 2026-10-13, because Table II has PPO *better* than `dijkstra_dynamic` at both grids, so a bare "not better" contradicts the paper.
- **Left out on purpose:** the Fig. 2 caption rule (triage rule 7), because its reason is code-level. P-21 carries an outside-fact flag, because the critique (§4.3) tags its claim about [2] [ext] even though its spreadsheet row doesn't.

## 14. Guide verified, and its webpage (2026-10-13)

`ABOT-red-team-explained.md` was checked line by line against the camera-ready text, the spreadsheet's "Without code access" tab and the triage. All 52 badges (priority, score, paper section), the at-a-glance table and the part assignments match. Every number traces to the paper, the triage, the red-team doc or a committed artifact. 16 wording fixes were made; the ones that matter on stage:
- **P-08:** the seed-3 block is *already bad at intact* (≈16.9) and slightly better at severe/extreme (≈22.9). "Just as bad at intact" was loose.
- **P-18:** the gossip ablation is no longer called "a transport-cost check". The red team found no gossip packet is sent at evaluation (§11), so even transport wasn't exercised there. On stage: "Gossip made no difference; its merge step isn't connected yet."
- **P-05:** only `dijkstra_dynamic`'s PDR responds *materially* to damage (others move by < 0.02), not "at all".
- **P-32:** the 4.7× at 10×10 is not printed in the paper; it comes from `results_rev1/scalability.csv`. A listener holding the paper knows only 7.3×.
- Quotes made verbatim: "roughly 4.4% channel occupancy", "extreme network collapse", ROUTE_UPDATE, and the KS-test "PDR" (the paper never says "network PDR").

**The webpage.** `ABOT-red-team-explained.html` (standalone, works offline) is generated from the markdown by `tools/explained-page/build.py` (styles and script in `page.css` / `page.js` beside it). Don't hand-edit the HTML: edit the markdown, then run `python -E -P tools/explained-page/build.py --fragment <path>`. The script stops if the markdown loses the structure it expects. The page reuses the study page's palette and fonts. It has search over points, rules, checklist and glossary, a filterable and sortable 52-point index, problem N beside reason N in each entry, a "talk actions only" view, and a slide checklist whose ticks are saved per browser. A private claude.ai copy is at https://claude.ai/artifact/GzJsxJdhCD5eMXaTPs6Ma4. To update it, publish the `--fragment` output to that URL, together with page 2 (§23).


## 15. Negative tests, and whether the code fixes P-04 / P-05 (2026-10-13)

**Negative tests exist** (read, not run). About 10 tests expect an error: `n_safe_zones` of 0 or −1 (`tests/test_boundary.py:168-181`), an unknown severity name (`test_channel_severity.py:47`), a payload over the 51 B MTU (`test_comm.py:164`), an unknown reference agent in the stats (`test_eval.py:517`). Roughly 50 more, counted by test name, break something on purpose: a dead neighbour chosen gives −20 and no move (`test_nav.py:109, 697`), every node failing (`test_boundary.py:76`), a disconnected 5 km grid (`:120`), TTL 0 (`:198`), collisions under 6 dB (`test_contention.py:140, 302`), no path to a safe zone (`test_adaptive_baselines.py:79`). They check that the code rejects bad input or doesn't crash. **None checks that a weak link can make a hop fail, or that success drops when the task gets hard.** The disconnected-grid and mass-failure tests check only "no crash" and "episode ends"; the test that sets a node's link score to 0 (`test_nav.py:707`) checks only that the reward falls.

**P-04 and P-05 are not fixed in the code.** Nothing was solved and left out of the paper:
- `DisasterEvacEnv` has no option for channel-gated hops (`env.py:84-103`); a hop needs only a live neighbour (`:311-313`). `strict_action_space` is about the 8-slot limit, not this.
- Every evaluation uses 400 m spacing and the fixed 1500 m range (`topology.py:20`; `run_monte_carlo.py:70-95`). No sparser run exists.
- No route-level or multiplied ("end-to-end") delivery figure exists. The score is averaged per step (`runner.py:103-104`, `run_monte_carlo.py:109-110`).
- **Trap:** `src/eval/figures.py:117` calls a plot "mean end-to-end PDR", but it plots `final_pdr`, the node score at the route's last node (`experiments.py:351`). It isn't end-to-end and isn't in the paper.
- **Raw material only:** the SimPy backend logs when each message first reached each node (`sim/mesh.py:268-284`). Filtering that log to SOS messages at gateways would give SOS delivery and delay, but nothing does it, and the evaluated timestep backend keeps (message, receiver) pairs with no times (`timestep.py:221, 569-570`). Getting the figure needs new code and new runs.
- What the code *does* add for P-04 is the meaning of the number (§11), which the paper never states. The audit notes show the ceiling was known and handled by comparing route length instead (`<CODE>/REVISION-WORKORDER.md:130, 334`).

**Defence hooks for P-04 / P-05 in the paper's own text** (checked 2026-10-13 against the docx):
- III, reward: the link-quality term is "a soft preference rather than a constraint". IV: backend equivalence "holds for liveness, what the agent trains against". So the paper already says the task is about node liveness, with link quality as a cost, not a pass/fail gate. That's the honest frame for P-05.
- V-C: "mean PDR falls with path length, so matching on steps widens the separation to 1.9–2.6×", and "The contrast is conservative". This answers P-04's "averaging rewards longer paths": here longer routes score *lower*, and the dynamic planner still wins.
- V-D: "Severity therefore bites on the longer links, which is how structural damage removes the mesh's long-range shortcuts" (1500 m PDR 0.109 at extreme; 400 m links stay above 0.73). A sharp listener can set this against ceiling success; answer that hops aren't gated by link quality in this version.

**Code and data facts behind the P-04 / P-05 answers** (2026-10-13; computed from committed CSVs and the phy formulas, nothing in `<CODE>` run):
- **Route cost is ETX-shaped.** `dijkstra_dynamic` sums 1/score per hop (`baselines.py:339-342`, score = mean of the two endpoint node scores). So route *choice* accounts for weak hops piling up, even though the reported metric is an average.
- **The score falls with route length in all five agents at both grids** (10×10 `dijkstra_static`: 0.253 / 0.139 / 0.090 at 1 / 2 / 3 steps). That backs the paper's "conservative" claim; the matched-step table is in `results_commaware/FINDINGS.md` §5.
- **At intact through heavy the score measures collisions, not the channel.** Recomputed from Table I with mean path loss (what the timestep backend uses): every in-range link delivers ≥ 99.96%. At severe, links beyond ~1.1 km fail (1131 m: 2.6%); at extreme, beyond ~0.8 km. The paper's own Fig. 2 explains the V-B step: the PDR = 0.5 distance is 2.0 km at heavy (outside the 1.5 km neighbour range) and 1.03 km at severe (inside it).
- **The score is very skewed.** For 10×10 `dijkstra_static`, the median is 0.043 and 26/100 runs score exactly 0.
- **`dijkstra_dynamic` detours.** It is never shorter than `dijkstra_static` and is longer in 63/100 runs. In 10 of the 23 seeds where the safe zone is one hop away, it takes 2–5 hops. It deviated from its initial plan in 76/100 (`pair_mechanism.json`). Don't claim the extra hops are "worth it".
- **Node failure barely touches a run.** All nodes are alive at every reset (`timestep.py:195-200`); "graceful" failures take 300 s to kill. At λ = 1/3600 with 10 s warm-up + 10 s per step, P(a node on the route dies) is ≈ 0.8 / 1.6 / 2.7% for 2 / 3 / 4-step runs. The paper states λ, the step length and "mixed", so a listener can work this out. Burst mode is described in III but never evaluated; IV-A already says "higher failure rates are untested".
- **Success:** the classical planners succeed in every run in every file. PPO's only failures are seed block 3 (49/50 per preset), i.e. the livelock, never damage.

## 16. P-01 in the code: what exists, and the "next step" framing (2026-10-13)

Read, not run. **P-01 isn't solved and isn't "measured but unreported".** SOS traffic is simulated, but it isn't the traffic the compared methods route, and nothing checks it at a rescue node:
- **SOS messages exist.** One at reset, then one every 10 steps from a random live node other than the agent (`env.py:290-291, 317-319, 390-409`).
- **They're broadcast floods with no destination.** `_inject_sos` passes no `dst`, so it defaults to broadcast (`timestep.py:342`). Geo-greedy unicast exists and has a test (`timestep.py:668-700`; `tests/test_timestep_provider.py:194`), but no episode uses it. The paper's "propagates hop-by-hop toward progressively better-connected neighbours until it reaches an active rescue node" (III) describes something the evaluated runs don't do.
- **Gateways do nothing in the radio layer.** `is_gateway` is used only to end the agent's episode (`env.py:344`), in the observation, and to exempt gateways from failures. No code checks whether an SOS reached one.
- **The routes being compared carry no packets.** A hop just moves the agent's position (`env.py:312-313`). The SOS floods are independent of which method is driving, so an end-to-end figure taken from them would measure the Gossip3 flood, not Dijkstra vs PPO.
- **The timestep backend can't time an SOS.** `advance()` runs the whole flood (up to 20 rounds, `timestep.py:49, 489`) inside one 10 s step and logs (message, receiver) pairs with no time (`:221, 567-571`). Every SOS reaches whatever it reaches in the step it was sent, whatever the 2.47 s SF12 airtime per hop. The SimPy reference does log first-arrival times (`sim/mesh.py:268-284`), but no paper result uses it for routing.
- **Trap:** "Evacuation latency CDF" (`eval/metrics.py:82-97`, `eval/figures.py:69`) is a step count, not message delay. It isn't in the paper.

**Paper wording that bears on the framing** (docx, checked 2026-10-13):
- I: "Its aim is to establish that substrate and a baseline comparison, not a deployment-ready routing policy." "Baseline" in the paper means the four classical planners and the comparison against them, not a delivery reference value.
- VII: "Hardware validation and integration with SAR platforms remain as immediate next steps". The same paragraph says "The ablations locate the measured delivery gain in live link state alone", and the abstract says "improved packet delivery performance". Both claim delivery that nothing measures.

**What the honest next step involves:** send the SOS along each method's chosen route over the radio model, with hops that can fail (this is P-05 too), in a backend that keeps time (SimPy, or a timestep backend changed to spread a flood across steps and use shadowing). Then record arrival at a rescue node and the delay. That gives a simulator prediction a Meshtastic testbed can check. Running the current timestep backend as it is would mostly measure its collision artefacts (§11, §15).

## 17. P-05 in the code: what exists, and the "next step" framing (2026-10-13)

Read, not run; the numbers below come from committed CSVs. Extends §15. **P-05 isn't solved, and nothing unreported answers it.** Success is measured; it sits at 100% because of how the task is built.
- **Knobs exist, but no run used them.** `spacing_m`, `lambda_fail`, `failure_mode` (including burst) and `burst_radius` are env arguments (`env.py:84-103`). Every paper run used 400 m spacing, λ = 1/3600 and mixed failures. The 1500 m neighbour range is a fixed constant (`topology.py:20`) and is the same at every damage preset, so damage never removes a neighbour. Sparser meshes and harsher failures need only settings changed (plus PPO retraining); hops that can fail need new code.
- **A failure-rate stress test exists but is legacy and was never run for the paper.** `FailureStressTest` (`src/eval/experiments.py:262-360`) sweeps λ from 0 to 0.5 s⁻¹ on 5×5, on the SimPy backend, with the old agent set (`dijkstra`, `comm_dijkstra`, `astar`; no dynamic planners, no PPO). Its only caller is `scripts/generate_paper_figures.py:86`, and the figure that would write (`figures/fig4_pdr_vs_failure.png`) doesn't exist. Its tests (`tests/test_eval.py:107-130`) check only the record count, that success lies in [0, 1], and that success = 1 at λ = 0. It tests node death, not weak links.
- **Trap:** `darwinV2/figures/_test_fig4.png` ("PDR vs failure rate") comes from a plotting unit test with made-up curves (`tests/test_eval.py:255-262`). Never show it.
- **Damage changes nothing for the static planners.** In `results_commaware/commaware_severity_episodes.csv`, `dijkstra_static` and `astar_static` take the same number of steps at all five presets in 250/250 episodes (mean 2.10) and succeed in 1,250/1,250. In `results_rev1/damage_severity.csv`, `astar_dynamic` also averages 2.10 at every preset. `dijkstra_dynamic` moves only between 3.04 and 3.13 steps, and PPO between 2.35 and 2.40 (success 0.996 throughout, all from the seed-3 livelock).

**Paper wording that bears on P-05** (docx, checked 2026-10-13):
- V-A discloses the ceiling: "Success is at ceiling for all five agents at both grid sizes, so they separate on path efficiency rather than task completion." That's disclosure, not a fix, and it's the best hook.
- II says "Adaptive routing is rarely benchmarked across infrastructure degradation" and that the "five-preset severity sweep" addresses it. So the paper presents the sweep as a contribution; calling it "just a baseline" on stage contradicts that.
- V-D: "Severity therefore bites on the longer links, which is how structural damage removes the mesh's long-range shortcuts." In the routing runs those shortcuts stay neighbours and every hop to them succeeds.
- IV-A: "larger grids and higher failure rates are untested." None of the five listed limitations (VI) says that hops aren't gated by link quality.

**Framing:** the next step for P-05 is to *change the task*, not to *measure* something. P-01 and P-05 share one fix: send the SOS along each method's route over the radio model with hops that can fail, on sparser meshes. That experiment gives success under damage, SOS delivery and delay together. In the current timestep backend, gating hops alone would barely bite: with no shadowing, every in-range link works ≥ 99.96% at intact–heavy, and only the long links fail at severe/extreme (§15). It needs shadowing on and sparser meshes too, plus a link model calibrated on hardware.

## 18. P-07 in the code, and the "no dataset, wait for hardware, it's a PoC" framing (2026-10-13)

Read, not run. **P-07 (the winning planner is scored on the number it optimises) isn't solved.**
- The circle is literal. `dijkstra_dynamic`'s edge cost is 1/score (`baselines.py:339-342`); the reported result is the average score at the nodes the agent lands on (`env.py:340`, `runner.py:103-104`).
- Every per-episode file holds only success, steps, reward and `mean_pdr_seen` (`results_rev1/baselines.csv`, `results_commaware/*.csv`, `results_15x15/statics_15x15.csv`). Paths aren't saved, so even the channel model's per-hop odds along the routes taken can't be computed afterwards. Routes carry no packets anyway (§16).
- The paper's supporting checks (matched steps 1.9–2.6×, the 43-seed subset 1.50×, the A\* null) all use the same score. They rule out path length and isolate replanning; they don't break the circle.
- The score is a weaker proxy than it sounds: a link never tried counts as 1.0 and every failed try as 0 (`timestep.py:538-545, 728-733`), so a node can score high by having sent little. Code-level; the audience can't raise it.

**Verdict on framing P-07 as "no dataset represents delivery faithfully; that's for the hardware stage; this is a PoC": don't use it as the answer to P-07.**
1. Wrong question: the circle is a choice of metric inside the simulator. Field data wouldn't remove it; a different metric would, and the simulator's channel model can already score each hop.
2. It contradicts the paper: abstract "improved packet delivery performance"; VII "The ablations locate the measured delivery gain in live link state alone".
3. "No dataset" clashes with III: the path-loss exponent is "based on IEEE 802.15.4a CM6 measurements and post-earthquake LoRa field data [10]".
4. Hardware fixes realism, not circularity: measuring the same beacon score on a testbed is still circular.
5. Order: hardware checks a simulator prediction, and no simulated delivery figure exists yet.
6. "Proof of concept" isn't in the paper. Its words are "exploratory", "entirely in simulation", and "Its aim is to establish that substrate and a baseline comparison, not a deployment-ready routing policy" (I).

**The usable half:** "absolute numbers need hardware" is sound (III "unvalidated against ABOT hardware"; IV KS tests; VI simulation-only), as an answer to "how realistic is the channel?" (§12 / triage Q3), not to P-07. **For P-07:** concede the circle, claim only that live link state changes which routes get picked, and name the next *simulation* step (send the SOS along each route with failable hops; count arrivals and delay), with hardware checking it afterwards. Same fix as P-01 / P-05 (§16, §17).

## 19. P-12 in the code: what PPO actually sees, and the "lower bound" (2026-10-13)

Read, not run. **P-12 isn't solved: the paper still says "lower bound", and nothing measures either asymmetry.**

**PPO's inputs, by where they come from** (`src/nav/state.py`; both backends build the snapshot it reads, `timestep.py:711-760`, `sim/mesh.py:184-200`):
- **Whole-network, as P-12 says.** The hop count to the nearest alive gateway is a breadth-first search over every node's alive-neighbour list (`state.py:164-166, 190-222`). The direction to the nearest *alive* gateway needs gateway liveness (`:145-162`). In mixed mode gateways can fail: every node gets a failure time, and only burst exempts gateways (`timestep.py:245-247`). In 2–4 step episodes this almost never happens, so that direction nearly always equals the plain safe-zone bearing in features 6–7.
- **A further leak, visible only in the code.** The 8 "neighbour PDR" slots, and the minimum-neighbour-PDR feature, read each neighbour's *own* node-level score from the snapshot (`state.py:135-138, 176`), not the agent's link to it. III says "a beacon's payload is the sender's identifier alone" (and `timestep.py:463`), so a real node couldn't know those values.
- **Even the "local" inputs come from the simulator, not from listening.** In both backends `rssi_map` is every *alive* in-range neighbour, with RSSI taken straight from the channel model (a static mean in timestep, a fresh draw in SimPy). `reachable_neighbors` counts alive neighbours. Nothing comes from beacons heard, and in the timestep backend every beacon collides anyway (§11). Only position, battery, elapsed time and the fixed safe-zone geometry are local in the plain sense.

**The "lower bound" is asserted, not measured:**
- No run measures either asymmetry. `strict_action_space=True` (`env.py:64-79`) would hold the planners to PPO's 8 slots, but it appears only in tests (`tests/test_nav.py:262-319`). Planners always get the full snapshot (`runner.py:93-97`), and there is no switch for a local-only planner or for PPO without the whole-network features. `src/eval/ppo_ablation.py` tunes hyperparameters, not inputs.
- Partial evidence points the other way for the 8-slot asymmetry. `results_rev2/action_space_audit.json`: `dijkstra_dynamic` uses an index beyond slot 8 in 73/310 moves (23.6%), `astar_dynamic` in 1/217 (0.5%). The counts vary slightly run to run (the file records ~25% and 0.5–0.9% from other runs). So the fast planner PPO trails at 10×10 barely uses the extra freedom, and PPO beats the planner that uses it most. The red team's constant action-0 policy (§11, `redteam/seed_starts.py`) shows an optimal next hop is always within the 8 slots on the evaluation seeds. The slot limit does cause the seed-3 livelock (VI).

**Paper wording** (docx, checked 2026-10-13):
- III: the planners "receive the full global network-state snapshot …, whereas the agent sees only the local observation", and "Both asymmetries run the same way, so the comparison is conservative with respect to the learned agent on two counts rather than one."
- V-A: "both run against PPO, so its position is a lower bound rather than a like-for-like result."
- III's own feature list includes "hop count to that gateway", so a listener can catch this from the paper alone.

**Framing:** "measure" fits here, unlike P-05, but the result could go either way: the evidence so far says the slot limit doesn't cost PPO route length, and PPO is handed whole-network hop counts. So don't promise a direction. The useful next step is to give PPO only what a node can learn from messages it receives (e.g. beacons carrying the sender's hop count and score), retrain, and measure the change. That both tests the claim and is a prerequisite for running PPO on boards. It doesn't help validate the simulator. The planners have the same gap (P-03): on hardware, neither method gets the map the simulator hands it until the protocol carries routing information, which costs airtime.

## 20. P-18 in the code: the gossip ablation (2026-10-13)

Read, not run. **P-18 isn't solved: nothing in the code ever uses a received gossip value.**
- **Receive side is empty.** `absorb_incoming_gossip` is a `pass` stub marked "deferred to Module 4" (`src/nav/gossip.py:211-222`). `merge_q_tables` and `decode_q_table` are only exported and unit-tested. Neither backend decodes a GOSSIP payload; the packet type is only forwarded and suppressed like any other. No observation feature reads gossip values (`state.py` has none).
- **Zero gossip at evaluation (confirms the red team).** Every reset builds a fresh scheduler with an empty table (`env.py:280-288`), `inject` returns on an empty table (`gossip.py:200-201`), and the ablation's evaluation loop (`scripts/run_gossip_ablation.py:142-146` → `run_episode`) never fills it. The 300 "on" test episodes ran in the same network as "off".
- **Refinement: some gossip does go out in training.** `GossipCallback` fills the table at the end of each 200-step rollout (`ppo_trainer.py:170-203`), and the send check runs before the step counter ticks (`env.py:322` vs `:348`). So an env that has just auto-reset at a rollout boundary sends one packet on its first step, and long early-training episodes send more. "Rare once episodes are short", not "never". The verdict doesn't change: nothing reads the content.
- **"Per-node V(s) has no meaning" is the weakest sub-point.** It's the critic's value averaged over the visits to that node in the last rollout: coarse (it blurs time and link quality) and policy-dependent, but defined. The node is recovered from (x, y) by nearest grid position, which is exact.
- **Only one gossip experiment exists** (`results_rev1/gossip_ablation/`, 10×10, default failures). No larger-grid or higher-failure run.

**Paper wording that carries the defence** (IV-A, docx): "implemented but not wired into the receive path, so the results here exercise gossip transport and its airtime cost only"; "This is evidence that the pipeline does not depend on gossip, not evidence that gossip helps"; "Both arms already solve the 10×10 task". VII: "neither the learned policy nor the Q-value gossip channel adds to it yet". The one sentence that's wrong at evaluation is "the enabled arm pays gossip's airtime"; only code access reveals that, and the paper links no code.

**Framing:** a disclosed null, i.e. a check that the system works without gossip, run because R1 asked for an ablation. Testing whether gossip *helps* needs the merge wired in and a task that isn't at ceiling.

## 21. P-22 in the code: what each "PDR" is (2026-10-13)

Read, not run. **P-22 is valid and not solved; the code actually has more PDR-named quantities than the three the red team lists.** None is SOS delivery to a rescue node.

| What the paper calls it | What the code computes | Where |
|---|---|---|
| Fig. 2 "PDR" vs distance (V-D) | Analytic single-link delivery chance from the channel formulas, averaged over 5,000 shadowing draws. Not a mesh run, despite the caption's "timestep backend". | `scripts/make_fig4_pdr_distance.py:1-40` |
| (not named) the evaluated backend's per-link chance | Same formulas with mean path loss and **no shadowing**, so ≥ 99.96% for every in-range link at intact–heavy. The equivalence script's own note admits this. | `timestep.py` PER cache; `benchmarks/run_backend_equivalence.py:17-26` |
| III's per-link PDR "from arrival statistics over a sliding window of 50 packets" | Last 50 transmit attempts on link (tx, rx), recorded on the **transmit side** from the simulator's outcome, all traffic types. | `timestep.py:538-545` |
| "local PDR", "eight neighbor PDRs", min-neighbour PDR, PDR trend (III obs.); "−0.5·(1 − PDR)" (reward); "PDR-weighted" edges and "PDR falls below 0.5" (V) | **One node score:** mean of that node's ~30 link windows, untried link = 1.0. | `timestep.py:720-733`; `state.py:103-104, 138, 172, 176-177`; `env.py:340-341`; `baselines.py:312-320, 339-342` |
| V-B / V-C "mean link PDR" (0.267 vs 0.145) | That node score at the node the agent lands on, averaged over the episode's steps (`mean_pdr_seen`). | `runner.py:103-104`; `results_commaware/run_commaware.py:135` |
| IV KS-test "PDR" | Share of injected (SOS) messages heard by at least one other node; beacons excluded. Same definition in both backends. | `timestep.py:382-402`; `sim/mesh.py:212-221` |
| Abstract "improved packet delivery performance"; VII "measured delivery gain" | Nothing. No SOS-at-rescuer count exists (§11, §16). | — |

- **Simplifying fact for the defence:** every PDR used *inside* the routing task (observation, reward, planner, the V-B/V-C result) is the same node score. So the paper really has three: the channel-model curve, the node link-quality score, and network reach.
- **Only one of the three carries a claim.** Fig. 2 is scoped as "internal consistency of the channel model only"; the KS PDR is reported as *differing* between backends and isn't used for any result. The V-B/V-C score carries the supported result, and it's the one the paper never defines.
- **Trap:** `src/eval/figures.py:110-117` labels a plot "mean end-to-end PDR"; it plots `final_pdr`, the node score at the route's last node (`experiments.py:351`). Not end-to-end, not in the paper.
- **Safe on-stage gloss of the result's metric:** "a link-quality score each node keeps for its links, averaged over the nodes the route visits". Don't say it comes "from beacons" or is measured on the receiver side; the code does neither.

## 22. P-14: the evaluated model is the least-settled one (2026-10-14)

- **The PPO model behind every Monte Carlo and severity result is seed 0** (§7), and `results_rev1/convergence_summary.json` gives seed 0 a final explained variance of **−0.666**: the worst of the three (seed 1 0.184, seed 2 0.709).
- **A listener can work this out from the paper.** VI prints "−0.67, 0.18, and 0.71 across the three training seeds" in seed order. So the triage's backup line for P-14 ("one trained model, seed 0") invites the follow-up "the −0.67 one?". Have the answer ready: yes; it still reaches the safe zone in a similar number of steps to the planners, but the paper doesn't measure how PPO's numbers vary across training runs.

## 23. Q&A prep plan: the user's chosen points, reviewed (2026-10-14)

The user picked 28 of the 52 P-points to prepare for Q&A, in 17 sets: P-01, {P-02, P-41}, P-03, P-04, P-06, {P-07, P-13}, {P-10, P-11}, {P-05, P-18, P-35, P-30, P-40, P-01, P-25}, P-15, P-12, P-52, P-31, {P-28, P-45, P-21, P-23}, P-43, P-16, P-20, P-22. P-01 is listed twice. They asked for a critical review.

**The review** is `ABOT-qa-prep-plan.md` (the source), also shown as page 2 of the explained webpage and as the "Q&A prep review" sheet of `ABOT-red-team.xlsx`. The rule it applies: points share a set when their answers start with the same sentence, not when they share an ending such as "…that's future work". Findings:
- **Coverage is right.** All 10 triage "have an answer ready" points are included.
- **Misfits in the big set:**
  - P-40 is a mistake in the paper (the 250-episode count belongs to the severity sweep), so "future work" is the wrong answer.
  - P-25 needs "what's new" first.
  - P-18 is a disclosed null.
- **One answer is split three ways:** P-04, P-07 and P-22 (with P-01).
- **P-13 belongs with P-05**, P-02 with P-05 (the time-scale point isn't just wording), P-41 with P-15, and P-21 with the radio points (not the livelock).
- **The radio points P-06, P-20, P-16 and P-43 are one story.**
- **P-12 is the trap inside "why RL?".**
- **Suggested additions:**
  - P-08: the abstract, the likeliest gap.
  - P-32, P-17, P-24: the simulator. The "what's new" answer leans on it.
  - P-38: the sibling of P-40.
  - P-14.
  - P-42: Section I gives the reason for RL as replacing Dijkstra and handling spatially correlated failures, so P-30 surfaces through "why RL?".
  - P-27 only if a slide names the path-loss source.
- **Regrouped into 9 sets (A–I)**, each with an opening line to learn.

**Building it.** `python -E -P tools/explained-page/build_plan.py [--artifact PATH] [--xlsx]` writes `ABOT-qa-prep-plan.html` and, with `--xlsx`, rewrites only that sheet.
- **Checks:** the script stops if the per-point table disagrees with the guide's at-a-glance table, if a set's points don't match the table, or if "Your list" names different points.
- **Spreadsheet:** openpyxl drops cached formula results on save and there's no LibreOffice on the prep machine. The script therefore writes them back into the XML, so the existing sheets' summary counts and the new sheet's counts still show without a recalculation.
- **Styles and links:** page 2 uses `page.css` + `plan.css` + `plan.js` and a plum `--plan` accent. Page 1 (`build.py`) now links to it from the bar, the hero and the contents rail.

**Publishing.** Inside the Artifact, page 1 is `index.html`, so page 2's links back point there. Publish both together: `build.py --fragment F` and `build_plan.py --artifact P`, then publish F to the URL with `files: {"ABOT-qa-prep-plan.html": P}`.


## 24. Literature gap (Section II) checked against the code (2026-10-15)

`ABOT-lit-gap-review.md` takes each Section II contrast and each of the three gaps, gives what the code supports and what counts against it, and offers safe wording for the user's own lit-gap slide, with a PDR section. The user asked for content only: **don't build slides or a deck** (no .pptx) unless asked.

New facts behind it (read, not run):
- **ABOT's own planner also recomputes on a trigger.** `dijkstra_dynamic` checks a fresh snapshot every step but recomputes only when one of the next 3 nodes dies or scores below 0.5 (`baselines.py:312-320`). Gap 2's contrast with "failure-triggered recomputation" holds only as "replans on degradation, before failure", not as continuous recomputation.
- **The paper faults [7] for not testing "progressive infrastructure failure", but ABOT doesn't test it either.** A route node dies in ~1–3% of trips, and burst was never run (§15). Keep this contrast off slides. The severity presets degrade links; they don't kill nodes.
- **No energy contrast with [8].** The planners' route cost is the link score only (`baselines.py:339-342`).
- **The cleanest framing of ABOT vs prior work on PDR:** prior work reports PDR as an *outcome* ([1] < 50% delivery; [7] delivery, delay, energy). ABOT uses a link-quality score as a routing *input*, and never measures the outcome.
- **Only the planner that replans on the score scores higher** (`results_commaware/FINDINGS.md` §5, not in the paper): dijkstra_dynamic 0.267, astar_dynamic 0.166, astar_static 0.161, dijkstra_static 0.145, PPO 0.141, the lowest. PPO sees the scores in its inputs and reward but gains nothing from them.
- **Citations on a lit-gap slide:** cite [8] as PARA [8] (not "Al-Hadhrami"). Don't attach [11] to IoT situational awareness (§7, §11).
- **Tooling:** pptxgenjs isn't installed globally on the prep machine; PowerPoint (`POWERPNT.EXE`) is, and there's no LibreOffice.

## 25. Plain-English results guide and slide-figure verdicts (2026-10-19)

`ABOT-results-explained.html` explains the six results in lay terms, marks every project-only fact in amber (tagged "helps", "weakness" or "know it", each with its source file), and gives a verdict on each figure and table for the slides. It is hand-written HTML (no build script). The figures it shows were copied to `assets/figures/` (300 dpi PNG plus vector PDF). Private claude.ai copy: https://claude.ai/artifact/FTFhT7Z93kaFUFzUsZhCo6. To update it, strip the `<!doctype>`/`<html>`/`<head>`/`<body>` wrapper into a fragment (keep `<title>`, links and `<style>`) and publish that with `files` mapping each `assets/figures/*.png` to itself.

**Figure verdicts** (only Fig. 1 and Fig. 2 are in the paper):
- `fig1_architecture_v2`: use; say "four layers" (the text says three).
- `fig4_pdr_vs_distance`: use; explain the log x-axis, and drop "timestep backend" from the caption (§21).
- `damage_severity`: use after relabelling. Its left panel's title and y-axis say "Packet delivery ratio", but it plots the node link-quality score. The "n=2.7" under each preset is the path-loss exponent, not a sample size.
- `fig_baselines`: backup only. Hop counts are integers, so the medians tie and PPO looks identical to `dijkstra_dynamic` (3 vs 3, 4 vs 4). Means (2.48 vs 3.23; 3.56 vs 4.40) show the gap. The reward panels repeat the steps story.
- `fig_scalability`, `fig_learning_curve`: backup. `gossip_ablation.png`: don't use; its title says "DARWIN v2".
- New charts drawn on the page from paper numbers: static vs dynamic link score (all trips, and the 43-seed subset); mean hops at both grids. Two more from project files: matched-step scores, and speed-up by grid size.

**New facts behind it** (read from committed files, nothing run):
- **The task is learned almost at once.** PPO's first logged mean episode reward (1,400 total steps) was 85.9 / 88.7 / 80.7 for seeds 0 / 1 / 2. It ended at 100.8 / 101.6 / 101.9 after 200,200. `timestep_90pct_reward` (7,000 / 9,800 / 15,400) is the total step at which the smoothed reward first reaches 90% of its own final value (`scripts/generate_paper_figures.py:622-692`).
- **Why 303× is so large:** SimPy gets much *slower* with contention off. At 15×15 it averages about 14.3 s per run without contention against about 0.53 s with it (`scalability_nocontention.csv` vs `scalability.csv`), most likely because more packets survive and get forwarded. The 303× is the λ = 0 run at 15×15.
- **Speed-up, pooled over the three λ values** (contention on): 7.2× / 4.7× / 4.0× / 3.5× / 4.5× / 4.1× from 5×5 to 30×30. The 20×20 dip comes from one timestep run (λ = 1/1800, seed 4: 1.64 s, mean reward −5384). With contention on, one of the 15 SimPy runs at 30×30 timed out (λ = 1/1800, seed 0).
- **The seed-3 block is one stuck trip.** At intact its success is 0.98 (49/50), and its mean steps of 2.39 is computed over the 49 successes. One failed episode drags the block's mean reward to ≈16.9.
- **Chart colours:** the study palette's teal (`--net`) and indigo (`--learn`) fail the dataviz validator's normal-vision separation check as a series pair (ΔE ≈ 12, floor 15). The page uses blue `#2a78d6` / `#3987e5` (planner that uses live scores) and orange `#eb6834` / `#d95926` (PPO), which pass in both themes, plus a grey for context.
- **Built-in browser, local files:** a `file://` page from this folder opens as a static `data:` snapshot. Relative images don't load there, and `#anchors` and `scroll_to` don't scroll it; use `scrollIntoView()` through the JavaScript tool instead.

## 26. Comparison with standard mesh protocols: OLSR, BATMAN-adv, Babel (2026-10-19)

`ABOT-vs-ICUAS2025-mesh-protocols.md` compares ABOT with Diniz, Ferrão, da Silva and Castelo Branco (University of São Paulo), "Comparative Performance Analysis of OLSR, BATMAN-adv, and Babel in UAV Mesh Networks", ICUAS 2025, pp. 496–503, DOI 10.1109/ICUAS65942.2025.11007820 (IEEE Xplore 11007820).
- **Only the public parts were read:** abstract, the four figure captions (packet loss, delay, CPU, RAM, each "under different loads"), 12 references and keywords. The full text is paywalled, with no free copy found. Device count, radio (almost certainly Wi-Fi), whether the Pis flew, and the numbers are all unknown.
- **WebFetch gets nothing from IEEE Xplore.** Open the page in the built-in browser and read `xplGlobal.document.metadata`, or same-origin `fetch('/rest/document/<id>/figures' | '/references' | '/citations')`, through the JavaScript tool.
- **Protocol facts, checked against the standards on 2026-10-19:**
  - OLSR: HELLO every 2 s and TC every 5 s (RFC 3626 §18.2); a HELLO lists neighbour addresses, 4 B each for IPv4 (§6.1).
  - Babel: UDP port 6696, ff02::1:6, multicast Hello every 4 s (RFC 8966 §5, App. B); wireless link cost in App. A.2.2.
  - BATMAN-adv: layer 2 only; the kernel docs show `orig_interval` 1000 ms.
- **Airtime arithmetic** (`tools/lora_airtime.py`, which re-implements `phy.py:54-88`): 1.32 s per 20 B frame and 2.47 s per 51 B frame at SF12; raw rate 293 bit/s.
  - At default timers, one node's own hellos would need about 132% (BATMAN-adv, 1 s, 20 B), 123% (OLSR, 2 s, 51 B) and 62% (Babel, 4 s, 51 B) of airtime.
  - An OLSR HELLO listing ABOT's mean 30.7 neighbours needs about 120 B of addresses, against a 51 B MTU.
  - Babel's IPv6 and UDP headers take 48 of the 51 B.
  - Caveats: the timers can be slowed, and header compression exists. ABOT never compared against any of these protocols, so no "ABOT beats X" claim is possible.
- **Code facts found while writing it:**
  - ROUTE_UPDATE is defined (`src/comm/packet.py:40`) and used only in `tests/test_sim.py:208`; the simulator never sends one.
  - No `.py` file in `darwinV2/` has a mobility model; node positions are fixed. Section III's "as nodes fail or move out of range" is half-simulated.
  - ABOT's own [1] says density *and traffic load* limit availability, yet no ABOT run varies the load.
- **The overlap to concede:** `dijkstra_dynamic` (shortest path, cost 1/score per hop) is OLSR-with-ETX in spirit, but with the map handed over by the simulator. Gap 2's contrast holds against [7] and [8], not against these protocols.

## 27. The talk deck (2026-10-20)

`ABOT-R10HTC-2026-talk.pptx`: 24 slides on the HTC 2026 template, 66 clicks, with the speech in the speaker notes.
- **Built, not hand-edited.** `python -E -P tools/deck/build_deck.py` (standard library only) reads `assets/template/HTC_2026_Presentation_Template.pptx`, `talk/speech-v2.docx` (a copy of the user's `SPEECH v2 conv.docx`) and `assets/figures/fig4_pdr_vs_distance.png`. Edit the script and rebuild; edits made in PowerPoint are lost on the next build.
- **QA:** `tools/deck/qa_render.ps1` opens the deck in PowerPoint (a clean open is the first check), flags text overflow and exports every slide before the first click and after the last. Its two width warnings on slides 12 and 13 are false positives. The pptx skill's `validate.py` passes against the template.
- **Fig. 1 slide (12)** shows the paper's architecture figure (`assets/figures/fig1_architecture_v2.png`). Three clicks frame the decisions-down arrows, the measurements-up arrows and the dashed harness box. The speech has no walkthrough of the figure, so its notes are written in `EXTRA_NOTES` in the script, with two "if asked" answers: PPO "may replace solver" (rule 4) and the planners' full network view (triage Q3). Slide 13 then starts on Layer 1; the paper's text says "three layers", but the slides say four (rule 10).
- **Notes:** the speech is cut per slide with `[CLICK n]` cues. The build stops if a cue no longer matches the speech or a slide's click count disagrees with its cues. After editing the speech, copy it over `talk/speech-v2.docx` and fix `CUES` in the script.
- **Animations** are written in the XML PowerPoint itself produces (captured from PowerPoint, then read back to check). Existing work shows names only; each name or subheader turns into a navy pill as it is spoken (an overlay that fades in, then out on the next click). B.A.T.M.A.N., Babel and OLSR sit on the gaps slide, cited as Diniz et al., ICUAS 2025 (§26), because the paper's reference list doesn't include them.
- **Wording follows triage §2:** the airtime limitation names no ETSI limit (rule 9); 7.3× is "up to", with 4.7× at 10×10 (rule 6); Fig. 2 is "from the channel model" (rule 7); "four layers" (rule 10); the link-quality score is defined as not delivery (rule 2).
- **Outside numbers:** slide 3 uses the WMO Atlas of Mortality and Economic Losses (2021): disasters 5× over 1970–2019, deaths down about 3×, losses 7× from the 1970s to the 2010s. These were checked against WMO and UN sources on 2026-10-20, and the slide cites them. Bangkok and Kashmir appear without numbers (not verified).
- **Speech lines that differ from the paper or code** (kept in the notes, not on slides):
  - "nodes ... move out of range": no mobility model (§26);
  - "two radios at opposite corners": both safe zones are corners of one edge (§11);
  - "15×15 ... for speed testing": 15×15 is also the second baseline grid;
  - "exceeds the 1 percent ETSI limit": see rule 9;
  - the R2 sentence "p values come well below 0.05" mixes the two comparisons.
- **Length:** the speech is about 4,000 words, roughly 27 minutes at a normal pace.
- **Tooling on this machine:** no python-pptx, markitdown, LibreOffice, pdftoppm or pptxgenjs. PowerPoint COM works for rendering (`Slide.Export`). In PowerShell, `$S` and `$s` are the same variable.
