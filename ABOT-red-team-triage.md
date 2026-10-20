# ABOT red team: what you can ignore for the R10-HTC talk

**Date:** 2026-10-13
**Input:** `ABOT-red-team.md` and `ABOT-red-team.xlsx`. They contain 82 points: 30 need the code (C-01 to C-30), and 52 can be made from the paper alone (P-01 to P-52).
**Question:** which of these can be ignored when presenting the camera-ready paper at IEEE R10-HTC 2026?

## Bottom line

- **47 of the 82 can be ignored outright** (§3).
- **25 need no Q&A preparation, only care with wording.** Don't repeat a particular sentence or number from the paper. They reduce to 13 rules (§2).
- **10 could realistically come up in Q&A.** They boil down to 6 questions. Add the 2 standard questions and you have **8 one-line answers to learn** (§1).

## Why so much can be ignored

1. **Nobody in the room has the code.** The paper has no code link or availability statement, so no audience member can raise any of the 30 C- points. Those points matter only where they rule out something you might say (§2).
2. **The paper is frozen.** Typos, citation mix-ups and the red team's journal-version fixes (its §16) can't change before the talk, and nobody spends Q&A time on them.
3. **Q&A is short.** In a few minutes, people ask big-picture questions: is it real, is the task too easy, how does it compare to existing systems. They don't ask about Holm families, slot synchronisation or reward bookkeeping.
4. **The red team's 1–100 rating is how hard a point is to defend once someone raises it, not how likely anyone is to raise it.** For a talk, likelihood is what counts. This triage adds that dimension.

---

## 1. Have an answer ready (8 questions)

| They might ask | Short, honest answer | IDs |
|---|---|---|
| **1. "Everyone reaches a safe zone ~100% of the time. Is the task too easy?"** | "Yes. Each node has about 30 neighbours, so most routes are only 2–3 hops. In this version a hop succeeds as long as the next node is still working, which is why we compare methods on route length. Next we'll make the task harder: sparser meshes, and hops that can fail on weak links." | P-05 |
| **2. "How many SOS messages actually reach a rescuer, and how fast?"** | "This paper doesn't measure that yet; it compares the routes each method picks. End-to-end SOS delivery and delay are the next experiment." | P-01 |
| **3. "With no central coordinator, how does a node know the whole network well enough to run Dijkstra?"** | "In the simulation the planners get a full view of the network, as a best case. Sharing link state across the mesh, and the airtime that costs, is future work." | P-03 |
| **4. "A 'link PDR' of 0.27, yet every route succeeds? Isn't the planner just maximising its own score?"** | "The number is a link-quality score for the nodes along the route, not the share of messages delivered. And partly yes: the dynamic planner uses that same score to choose its routes. So we only claim that live link state changes which routes get picked, with about 1.8× higher scores. We don't claim yet that it improves delivery." | P-04, P-07, P-22 |
| **5. "How does this compare with Meshtastic, or with mesh routing such as OLSR/ETX? What's new over [5]?"** | "We haven't benchmarked against those yet; our baselines are classical planners. Routing on measured link quality is a well-known idea. What we add is applying it to a gateway-free LoRa mesh across five damage levels, with a simulator fast enough for RL. [5] has hardware results and we don't. ABOT is meant to run as firmware on Meshtastic boards, so a head-to-head comparison is the natural next step." | P-10, P-11, P-25 |
| **6. "SF12, a beacon every 30 s and ~30 neighbours: won't the channel jam? Is that duty-cycle legal?"** | "It's a real limit, and the paper lists it. Beacons alone take about 4.4% of airtime per node, and with ~30 neighbours sharing the channel that adds up. Dense areas would need slower beacons or shorter, faster transmissions." | P-06 |
| **7. "Have you tested it on real hardware? How realistic is the simulator?"** (not a red-team item; it was the reviewers' main worry) | "Not yet; everything is in simulation. The channel is a standard path-loss model with five damage levels and a collision model. We've checked it for internal consistency only, not against real radio measurements. Next comes firmware on Meshtastic-compatible boards (T-Beam, Heltec, RAK)." | — |
| **8. "PPO doesn't beat Dijkstra. Why use RL?"** (not a red-team item) | "The RL part is exploratory. On this simple task PPO is in the same range as the classical planners, but not better. What we contribute is a simulator fast enough to train RL, plus an honest baseline. RL needs harder scenarios before it can show anything." | — |

These replace the older answers in `context.md` §9 for the talk. In particular, drop §9 Q1's "both asymmetries handicap PPO" argument (see rule 4).

---

## 2. Watch your wording (13 rules)

These points need no Q&A preparation. Just don't put the paper's version on a slide or say it out loud.

| # | Instead of (the paper's wording) | Say | IDs |
|---|---|---|---|
| 1 | "6.7 million deaths in the 1990s" [3] | **This figure isn't in [3]** (checked, see §6). Use no number, or one that *is* in [3]: yearly disaster damage rose from about US$20 billion in the 1990s to about US$100 billion in 2000–10, and 97% of disaster deaths since the 1960s were in developing countries. | P-09 |
| 2 | "improved packet delivery"; "the delivery gain"; "nodes measure link quality from beacons, and that's where the gain comes from" | "A planner that uses live link-quality scores routes through better-scoring nodes: about 1.8× higher." | C-01, C-07, C-09 |
| 3 | The abstract's "improved delivery under moderate degradation" and "limitations of RL under extreme collapse" | "PPO's results are flat across all five damage levels. Its one failure case comes from how its choices are set up, not from the damage." | P-08 |
| 4 | "lower bound", "the comparison is conservative against PPO", "PPO is intended to replace Dijkstra" | "PPO matches the classical planners on this task; it isn't better." | C-04, C-05, C-06, P-12, P-42 |
| 5 | Reading the 100% success, or the damage sweep, as robustness to damage; "damage removes the long-range shortcuts" | "Success is at ceiling, so we compare route length." | C-03, P-13 |
| 6 | A bare "7.3× faster", or "303×" | "About 4.7× faster at the 10×10 grid we used, and up to 7.3× on a small grid." 303× is with contention switched off, a setting no result uses. | C-20, P-32 |
| 7 | Fig. 2 captioned "timestep backend"; quoting "45.5 km"; implying the experiments used 11 dB shadowing | Caption it "PDR vs distance from the channel model". Call the presets relative stress levels. | C-02, C-14, P-15 |
| 8 | "multi-kilometre range without repeaters" | "About 2 km at the default damage level." | P-41 |
| 9 | "above the 1% ETSI limit" | "Beacon airtime is high: about 4.4% per node." ETSI EN 300 220-2 is a European standard, and the paper chose India's band. | P-20 |
| 10 | "three layers"; "ABOT, a device" | "Four layers" (matching Fig. 1). "A protocol that runs on existing LoRa boards." | P-39, P-50 |
| 11 | "steps-to-safe-zone are identical on all 100"; "250 episodes per preset" next to 0.267 vs 0.145 | "0.267 vs 0.145 over 100 matched episodes." Lead with ~1.8×. If you show the 43-seed 1.50×, call it a supporting check. | P-38, P-40 |
| 12 | "the enabled arm pays gossip's airtime" | "Gossip made no difference; its merge step isn't connected yet." | C-12 |
| 13 | "a representative 33-minute routing window" | Leave it out. Episodes actually last only a few steps. | P-02 |

---

## 3. Ignore (47)

| Why it's safe to ignore | IDs |
|---|---|
| **Needs the code**, and doesn't change what you'd say. (C-13, C-18 and C-28 have backup lines in §4.) | C-08, C-10, C-11, C-13, C-15, C-16, C-17, C-18, C-19, C-21, C-22, C-23, C-24, C-25, C-26, C-27, C-28, C-29, C-30 |
| **The paper is frozen:** typos, citation mix-ups, the figure count. Just don't copy them onto slides; for example, write "Olajide [8]", not "Al-Hadhrami". | P-27, P-36, P-37, P-49 |
| **Specialist statistics** | P-26, P-29, P-34, P-46, P-52 |
| **Protocol and radio details** a 12-minute talk won't reach | P-16, P-21, P-33, P-35, P-43, P-44, P-48 |
| **RL internals** (backup lines in §4 cover the seed and the livelock) | P-14, P-23, P-28, P-31, P-45 |
| **Simulator and ablation details** that the paper already discloses, or that matter only if you present them | P-17, P-18, P-19 |
| **Gaps in the literature review** | P-24, P-47 |
| **Already scoped, or easy to defend** | P-30, P-51 |

---

## 4. Backup lines (only if someone asks)

- **"Which of the three PPO models is in the results?"** "One trained model, seed 0. The 15×15 numbers use that same model, without retraining." (P-14, C-13, C-28)
- **"Did you compare PPO with a trivial rule?"** Only if asked directly: "Not in the paper. We've since checked, and a fixed 'always take the first listed neighbour' rule does nearly as well. That's another sign the task is too easy." (C-05)
- **"Do failures or battery drain even matter in episodes this short?"** "Barely. Episodes last a few steps, so those effects rarely come into play. Longer, sparser scenarios are next." (P-02)
- **"45 km at 'intact'? That's past the radio horizon."** "The damage levels are relative stress settings, not calibrated to measurements, and the paper claims internal consistency only." (P-15)
- **"ETSI doesn't apply in India."** "Right, it's a European rule. Either way, airtime at this density is the real constraint." (P-20)
- **"What was the livelock?"** "In one test scenario the policy kept picking a neighbour that had died. That one scenario recurs at every damage level. Hiding dead neighbours from the choice, known as action masking, fixes it." (P-23, P-45, C-18)
- **"Is 7.3× at your experiment size?"** "No. It's 4.7× at 10×10; 7.3× is on a 5×5 grid." (C-20)

---

## 5. What "ignore" doesn't mean

- **The code-level problems are real, and several hit the main results:**
  - hops never fail on weak links;
  - the main score is partly circular;
  - every beacon collides in the fast simulator;
  - the fast simulator has no random fading.

  You can leave them out of Q&A prep because nobody can raise them. But they're the reason the §2 rules exist, and any journal version would need them fixed (red-team §16).
- **Describe the protocol as a design** ("nodes beacon every 30 s to estimate link quality"), and **describe the results narrowly** (rule 2). Then nothing you say on stage is something you know to be untrue.
- **Optional, but worth it: one "Next steps" slide.** It would list:
  - hops that succeed or fail on link quality;
  - end-to-end SOS delivery and delay;
  - random rescue-node placement, with dead neighbours hidden from the agent;
  - hardware tests on Meshtastic boards.

  It answers questions 1–3 before anyone asks them. It also matches the paper's candid tone, which the reviewers rewarded.
- **Every detail on a slide invites a question.** Keep packet formats, the reward table, the 43-seed analysis and the gossip encoding off the main slides.

---

## 6. Checks made for this triage (2026-10-13)

- **[3] and the 6.7 M figure.** I searched the full text of [3] (IMF Working Paper WP/12/245, Laframboise & Loko, 2012, 32 pages) for death figures. It gives no death toll for the 1990s, and the figure 6.7 million doesn't appear. Its nearest statements are the damage and 97% figures in rule 1. Note that those replacement numbers come from [3], the paper's cited source, not from the camera-ready text itself.
- **Speedup.** I recomputed it with `redteam/speed.py` from `results_rev1/scalability.csv`. With contention on, it's 7.2× at 5×5, 4.7× at 10×10, 4.0× at 15×15 and 3.5–4.5× on larger grids. The paper's 7.3× is the 5×5 run with no failures (`results_rev1/logs/scalability.log:91`).
- **No code link.** The camera-ready text has no repository link or code-availability statement.
- **Coverage.** Each of the 82 red-team IDs appears exactly once in §1–§3.
