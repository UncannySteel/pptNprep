# ABOT red team, explained: the 52 points anyone can raise from the paper

**For:** presenting *ABOT: A Decentralized LoRa Mesh Communication Framework for Post-Disaster Environments* at IEEE R10-HTC 2026
**Date:** 2026-10-13
**Built from:** [`ABOT-red-team.md`](ABOT-red-team.md), [`ABOT-red-team.xlsx`](ABOT-red-team.xlsx) (tab "Without code access") and [`ABOT-red-team-triage.md`](ABOT-red-team-triage.md), checked against the camera-ready paper. This guide adds no new findings of its own: every point and number comes from those files or from the paper. Where a red-team quote didn't match the paper's exact wording, the guide uses the paper's wording.

## Contents

- [Start here](#start-here)
- [All 52 at a glance](#all-52-at-a-glance)
- [Part 1: Have an answer ready](#part-1-have-an-answer-ready) (10 points)
- [Part 2: Watch your wording](#part-2-watch-your-wording) (14 points)
- [Part 3: Safe to set aside](#part-3-safe-to-set-aside) (28 points)
- [Your slide checklist](#your-slide-checklist)
- [What still stands](#what-still-stands)
- [Glossary](#glossary)

## Start here

**What the red team did.** A red team is a deliberately hostile reviewer. Its job here was to find every way a tough critic could attack the camera-ready paper, before anyone at the conference does. It found 82 points:

- **30 need the code** (C-01 to C-30). The paper links to no code, so nobody in the audience can raise them. This guide leaves them out.
- **52 can be raised by anyone who has read the paper** (P-01 to P-52). This guide explains every one of them in plain English.

**What they mean for your talk:**

| | Points | What to do |
|---|---|---|
| 🎯 **Have an answer ready** | 10 | These could realistically come up in Q&A. They boil down to **6 questions**, each with a short, honest answer to learn. See [Part 1](#part-1-have-an-answer-ready). |
| ✏️ **Watch your wording** | 14 | Nobody is likely to ask about these, but don't repeat the paper's sentence or number. They boil down to **11 rules**. See [Part 2](#part-2-watch-your-wording). |
| 💤 **Safe to set aside** | 28 | They're real, but too detailed for a short Q&A, already disclosed in the paper, or frozen in print. Read them once so nothing surprises you. See [Part 3](#part-3-safe-to-set-aside). |

This sorting follows [`ABOT-red-team-triage.md`](ABOT-red-team-triage.md). The triage also prepares two standard questions that aren't red-team points ("Have you tested it on real hardware?" and "Why use RL?").

**How each entry is laid out.** Every point gets a plain-English title and a badge line, then three parts:

- **What it is:** what the paper says, and what a critic says about it.
- **Why it's an issue:** why that matters, in everyday terms.
- **Impact on your talk:** what to do on stage.

When a point bundles several problems, **What it is** and **Why it's an issue** number them the same way, so problem 1 matches reason 1.

**Reading the badge line.** Example: 🔴 **Critical** · Hard to defend: **75**/100 · Paper: V-C

- **Priority** is how much damage the point does if it holds:
  - 🔴 **Critical:** it undermines a headline claim.
  - 🟠 **Major:** it undermines a secondary claim or the paper's framing.
  - 🟡 **Minor:** presentation, citations or wording.
- **Hard to defend (1–100)** is how hard the paper's position is to justify once someone raises the point. 1 means a convincing answer exists; 100 means all you can do is concede. It is **not** how likely anyone is to raise it. A typo can't be defended, so it scores high, but nobody will ask about it.
- **Paper** gives the paper section the point is about.
- ⚠️ marks a point that relies on an outside fact nobody has verified yet. Check it before you quote it.

**Two cautions.**

- The suggested replies in the entries come from the red team and the triage. Where one says something is "next", "planned" or "future work", say it only if it matches your actual plans.
- A few entries mention what the red team found when it checked the code. Those notes only explain *why* a paper-level point holds. They aren't extra points to raise.

Technical terms are explained in the [Glossary](#glossary) at the end.

## All 52 at a glance

Sorted by ID. 🎯 = have an answer ready (with its question number), ✏️ = watch your wording, 💤 = safe to set aside.

| ID | The problem in one line | Priority | Hard to defend | For your talk |
|---|---|---|---|---|
| P-01 | The paper never measures whether an SOS reaches a rescuer | 🔴 Critical | 85 | 🎯 Q2 |
| P-02 | Episodes last seconds, not a 33-minute window | 🔴 Critical | 85 | ✏️ Wording |
| P-03 | The planner needs a full map the protocol never builds | 🔴 Critical | 85 | 🎯 Q3 |
| P-04 | The link scores can't be per-hop delivery chances | 🔴 Critical | 82 | 🎯 Q4 |
| P-05 | Every method succeeds, so the test can't show robustness | 🔴 Critical | 80 | 🎯 Q1 |
| P-06 | Beacons alone would saturate the radio channel at this density | 🔴 Critical | 80 | 🎯 Q6 |
| P-07 | The winning planner is graded on the score it chases | 🔴 Critical | 75 | 🎯 Q4 |
| P-08 | The abstract's damage claims contradict the paper's own results | 🟠 Major | 80 | ✏️ Wording |
| P-09 | The paper's opening death toll is probably misquoted | 🟠 Major | 80 | ✏️ Wording |
| P-10 | None of the baselines is a decentralised protocol | 🟠 Major | 78 | 🎯 Q5 |
| P-11 | Live link-quality routing already exists in mesh protocols | 🟠 Major | 75 | 🎯 Q5 |
| P-12 | PPO's 'local only' view includes whole-network information | 🟠 Major | 75 | ✏️ Wording |
| P-13 | Claim that damage removes long-range shortcuts is not shown | 🟠 Major | 75 | ✏️ Wording |
| P-14 | The paper doesn't say which trained model its results use | 🟠 Major | 72 | 💤 Set aside |
| P-15 | The channel model's distances and damage presets look miscalibrated | 🟠 Major | 72 | ✏️ Wording |
| P-16 | The packet sizes don't add up | 🟠 Major | 70 | 💤 Set aside |
| P-17 | The simulator match on alive nodes is nearly guaranteed | 🟠 Major | 70 | 💤 Set aside |
| P-18 | The gossip test was bound to find no difference | 🟠 Major | 70 | 💤 Set aside |
| P-19 | The replanning explanation contradicts itself | 🟠 Major | 70 | 💤 Set aside |
| P-20 | The airtime figure is miscalculated and cites the wrong rule | 🟠 Major | 68 | ✏️ Wording |
| P-21 | The channel model assumes timing the design doesn't describe | 🟠 Major | 68 | 💤 Set aside |
| P-22 | The paper uses PDR for three different quantities | 🟠 Major | 65 | 🎯 Q4 |
| P-23 | The livelock claim rests on one repeated scenario | 🟠 Major | 65 | 💤 Set aside |
| P-24 | Existing tools contradict the claimed research gap | 🟠 Major | 65 | 💤 Set aside |
| P-25 | The closest prior work already has hardware results | 🟠 Major | 62 | 🎯 Q5 |
| P-26 | Borderline 'PPO worse' verdict and strong 'indistinguishable' wording | 🟠 Major | 60 | 💤 Set aside |
| P-27 | The channel model cites a source for a different radio | 🟠 Major | 60 | 💤 Set aside |
| P-28 | PPO's eight choices depend on how the nodes are numbered | 🟠 Major | 60 | 💤 Set aside |
| P-29 | The 43-seed result was chosen after seeing the data | 🟠 Major | 58 | 💤 Set aside |
| P-30 | Clustered failures are motivated but never tested | 🟠 Major | 55 | 💤 Set aside |
| P-31 | The +5 reward pays for traffic the agent doesn't control | 🟠 Major | 55 | 💤 Set aside |
| P-32 | The speed-up headline hides its grid size and mode | 🟠 Major | 55 | ✏️ Wording |
| P-33 | Missed beacons can't be counted without sequence numbers | 🟠 Major | 55 | 💤 Set aside |
| P-34 | The comparison tests ignore that scenarios are paired | 🟠 Major | 50 | 💤 Set aside |
| P-35 | Nodes are assumed static, yet the paper mentions movement | 🟠 Major | 50 | 💤 Set aside |
| P-36 | The paper has harmless typos and formatting slips | 🟡 Minor | 95 | 💤 Set aside |
| P-37 | Two citations point to the wrong sources | 🟡 Minor | 85 | 💤 Set aside |
| P-38 | 'Identical on all 100' wrongly suggests the planners tie | 🟡 Minor | 85 | ✏️ Wording |
| P-39 | The text says three layers, the figure caption says four | 🟡 Minor | 80 | ✏️ Wording |
| P-40 | The 250-episode count is attached to the wrong comparison | 🟡 Minor | 75 | ✏️ Wording |
| P-41 | The multi-kilometre range holds only at milder damage levels | 🟡 Minor | 60 | ✏️ Wording |
| P-42 | Replacing the planner is an aim, not a result | 🟡 Minor | 55 | ✏️ Wording |
| P-43 | The 51-byte size limit is borrowed from LoRaWAN | 🟡 Minor | 50 | 💤 Set aside |
| P-44 | The 25% saving restates the chosen probability | 🟡 Minor | 45 | 💤 Set aside |
| P-45 | The livelock may be blamed on the wrong cause | 🟡 Minor | 45 | 💤 Set aside |
| P-46 | The headline ratios have no precision ranges | 🟡 Minor | 45 | 💤 Set aside |
| P-47 | The related work omits reinforcement-learning routing | 🟡 Minor | 40 | 💤 Set aside |
| P-48 | The paper doesn't mention half-duplex or listen-before-talk | 🟡 Minor | 40 | 💤 Set aside |
| P-49 | The paper's two figures don't show the main results | 🟡 Minor | 35 | 💤 Set aside |
| P-50 | ABOT is called a device, but no device was built | 🟡 Minor | 30 | ✏️ Wording |
| P-51 | Every route ends at one of two fixed safe zones | 🟡 Minor | 30 | 💤 Set aside |
| P-52 | The reward–steps link is built in, not discovered | 🟡 Minor | 25 | 💤 Set aside |

## Part 1: Have an answer ready

These 10 points could realistically come up in Q&A, from anyone who has read the paper or knows mesh networking. They boil down to six questions. Each question starts with a short, honest answer to learn. The entries under it explain the points behind it.

### Q1. "Everyone reaches a safe zone ~100% of the time. Is the task too easy?"

> **Your answer:** "Yes. Each node has about 30 neighbours, so most routes are only 2–3 hops. In this version a hop succeeds as long as the next node is still working, which is why we compare methods on route length. Next we'll make the task harder: sparser meshes, and hops that can fail on weak links."

*Points behind this question: P-05.*

#### P-05 · Every method succeeds, so the test can't show robustness

🔴 **Critical** · Hard to defend: **80**/100 · Paper: V-A; V-B

**What it is.** The paper says every method reaches a safe zone (the rescue point a route must reach) at its ceiling (its highest possible success rate), so the methods separate on path efficiency (how short their routes are). A critic raises three problems:

1. Every method succeeds about 100% of the time, at every damage level (the five presets, intact to extreme). The methods are four planners (classical route-finding methods) and the PPO agent (a reinforcement-learning route chooser, trained by trial and error).
2. Only one planner's score responds materially to damage, and only as a single step, between heavy and severe. Every other method moves by less than 0.02.
3. Routes are short: the paper's median routes are 2–4 hops (radio jumps) long, on a mesh where each node (one radio device) has about 30 neighbours on average (30.7).

**Why it's an issue.**

1. When every method succeeds, the test can't show which one copes better with damage. This is built into the simulation: the red team checked the code, and a hop always succeeds as long as the next node is still working, however weak the radio link.
2. If damage barely changes the results, the damage levels aren't really being tested: apart from that one step, the results look almost the same from intact to extreme.
3. Short routes on a dense mesh leave little room for one method to beat another, so the task is too easy to show robustness.

The task can't tell a robust method from a fragile one, so a reader may doubt that routing under damage was really tested.

**Impact on your talk.** **Have an answer ready** (Question 1). Don't present the ~100% success as evidence of robustness to damage. Say that methods are compared on route length, because success is at its ceiling (its highest possible level).

### Q2. "How many SOS messages actually reach a rescuer, and how fast?"

> **Your answer:** "This paper doesn't measure that yet; it compares the routes each method picks. End-to-end SOS delivery and delay are the next experiment."

*Points behind this question: P-01.*

#### P-01 · The paper never measures whether an SOS reaches a rescuer

🔴 **Critical** · Hard to defend: **85**/100 · Paper: Abstract; V; VII

**What it is.** The paper says a survivor's distress message (an SOS) travels hop by hop (one radio jump at a time) to an active rescue point, and that its results show "improved packet delivery performance". A critic raises three problems:

1. No end-to-end delivery ratio (the share of SOS messages that reach a rescuer, from start to finish): the paper never reports how often an SOS reaches a rescue point.
2. No delay (latency, how long a message takes to arrive): the paper never reports how long an SOS takes to arrive.
3. Its "mean link PDR" (PDR, packet delivery ratio, normally means the share of messages that get through) is never defined, and nothing it reports is delivery to a rescuer. Its conclusion still refers to "the measured delivery gain".

**Why it's an issue.**

1. For a disaster system, the core question is whether a distress message reaches help at all, and the paper cannot yet answer it.
2. In an emergency, how long a message takes matters too, and the paper gives no timing for SOS arrival.
3. The delivery wording rests on figures that don't measure delivery to a rescuer, so a critic can say the delivery claim is untested.

Overall, the system's central promise, getting an SOS to rescuers, isn't measured yet.

**Impact on your talk.** **Have an answer ready** (Question 2). This is the most natural question for a disaster-response audience. Never claim "improved packet delivery" or "the delivery gain" on a slide. Consider an optional "Next steps" slide that lists end-to-end SOS delivery and delay, so the answer is already on screen when someone asks.

### Q3. "With no central coordinator, how does a node know the whole network well enough to run Dijkstra?"

> **Your answer:** "In the simulation the planners get a full view of the network, as a best case. Sharing link state across the mesh, and the airtime that costs, is future work."

*Points behind this question: P-03.*

#### P-03 · The planner needs a full map the protocol never builds

🔴 **Critical** · Hard to defend: **85**/100 · Paper: III (routing layer); V

**What it is.** The paper describes a fully decentralised design, with no central coordinator, whose routing uses live network state for dynamic Dijkstra (a classic route-finding method, a kind of planner). A critic raises four problems:

1. Beacons (short radio messages used to discover neighbours) carry only the sender's ID, so they can't spread link-state information.
2. A route-update message type (ROUTE_UPDATE) is listed but never described.
3. The evaluated planners are handed a full, up-to-date snapshot of the network (a "global snapshot") by the simulation.
4. The radio time (airtime, the time a radio spends sending) that spreading link state would cost on a slow SF12 channel (a long-range setting of LoRa, a low-power radio) is not modelled.

**Why it's an issue.**

1. Without a way to spread link state, a node can't build the whole-network picture that global Dijkstra needs, so the protocol can't run it.
2. A message type that is listed but never described gives the protocol no defined way to share routing updates.
3. Because the simulator hands the planners the whole network, the results show what a planner could do with a complete picture, not what nodes can do with this protocol.
4. Sharing link state would use radio time, and the results leave that cost out.

The supported result holds only for an all-knowing ("oracle") planner, not for the decentralised protocol described.

**Impact on your talk.** **Have an answer ready** (Question 3). Don't imply the evaluated planner runs on the decentralised protocol as described. On slides, describe the planners as having a full view of the network, as a best case.

### Q4. "A 'link PDR' of 0.27, yet every route succeeds? Isn't the planner just maximising its own score?"

> **Your answer:** "The number is a link-quality score for the nodes along the route, not the share of messages delivered. And partly yes: the dynamic planner uses that same score to choose its routes. So we only claim that live link state changes which routes get picked, with about 1.8× higher scores. We don't claim yet that it improves delivery."

*What "for the nodes along the route" means: the red team checked the code, and the score averages all the links of each node the route visits, not just the links the route actually used.*

*Points behind this question: P-04, P-07, P-22.*

#### P-04 · The link scores can't be per-hop delivery chances

🔴 **Critical** · Hard to defend: **82**/100 · Paper: V-A; V-C

**What it is.** The paper reports about 100% success for every method, alongside a "mean link PDR" of 0.145 for static Dijkstra and 0.267 for dynamic Dijkstra. (PDR, packet delivery ratio, normally means the share of messages that get through.) A critic raises three problems:

1. Read as per-hop delivery chances (the chance that each hop, or single radio jump, works), 0.145 and 0.267 give end-to-end survival of about 1.5% vs 1.4% (0.145 to the power of 2.17 vs 0.267 to the power of 3.23, using average route lengths of 2.17 and 3.23 hops): a tie.
2. Both are absurd next to ~100% success, so the numbers can't mean what the paper implies.
3. Averaging per-hop values rewards longer paths and hides how losses compound hop after hop.

**Why it's an issue.**

1. On that reading the two planners tie, so the difference the paper reports between them would disappear.
2. Both figures clash with the near-100% success those planners achieve, so a reader can't take them as delivery chances.
3. Real losses multiply hop after hop, so longer routes should look worse. An average of per-hop scores ignores this, so it can't show how many messages actually get through.

The red team calls this only an illustration, since the number isn't a per-hop chance, but a reviewer who takes the paper at its word will do this arithmetic.

**Impact on your talk.** **Have an answer ready** (Question 4). Don't call 0.267 or 0.145 "delivery" or "the PDR of the route". Call them link-quality scores.

#### P-07 · The winning planner is graded on the score it chases

🔴 **Critical** · Hard to defend: **75**/100 · Paper: V-C

**What it is.** The paper's main supported result is that taking live link quality out of the dynamic Dijkstra planner lowers the "mean link PDR" along its routes (a link-quality score; PDR normally means the share of messages that get through) from 0.267 to 0.145. But that planner *chooses* its routes using PDR, and is then *scored* on PDR. A critic will say: remove the thing a planner aims for, and of course it scores lower on that thing.

**Why it's an issue.** It's like coaching a student on one practice test and then grading them on that same test: a higher mark shows the coaching worked, not that they learned more. The result shows that live link quality changes which routes get picked. It doesn't show that more messages get through, which is what the paper's "improved packet delivery" suggests.

**Impact on your talk.** **Have an answer ready** (Question 4). On slides, describe the result narrowly: live link-quality scores change the routes, giving about 1.8× higher scores. Never say "better delivery" or "the delivery gain".

#### P-22 · The paper uses PDR for three different quantities

🟠 **Major** · Hard to defend: **65**/100 · Paper: III; IV; V

**What it is.** The paper uses "PDR" (packet delivery ratio, normally the share of messages that get through) throughout. A critic points out that the term covers at least three different quantities:

1. Fig. 2's "PDR" is the channel model's prediction at a given distance (the channel model is the formulas for how radio signals weaken with distance).
2. The results' "mean link PDR" (V-B and V-C) is never defined.
3. The PDR compared in the KS tests (a statistical check that compares the two simulators) is a third, different quantity. The red team checked the code: it counts a message as delivered as soon as any one other node (radio device) hears it.

**Why it's an issue.**

1. A prediction for a radio link at a given distance is not a measurement of messages reaching rescuers, so Fig. 2 cannot support a delivery claim.
2. A key measure is left undefined, so a reader can't check what the number means.
3. The KS-test PDR counts a message as delivered as soon as one other node hears it, so it can't stand in for delivery to a rescuer.

None of the three is SOS delivery, and a reader can't tell which PDR a number means.

**Impact on your talk.** **Have an answer ready** (Question 4). On slides, label each number precisely, for example "link-quality score along the route" or "PDR vs distance from the channel model". Never use a bare "PDR" for two different things.

### Q5. "How does this compare with Meshtastic, or with mesh routing such as OLSR/ETX? What's new over [5]?"

> **Your answer:** "We haven't benchmarked against those yet; our baselines are classical planners. Routing on measured link quality is a well-known idea. What we add is applying it to a gateway-free LoRa mesh across five damage levels, with a simulator fast enough for RL. [5] has hardware results and we don't. ABOT is meant to run as firmware on Meshtastic boards, so a head-to-head comparison is the natural next step."

*Points behind this question: P-10, P-11, P-25.*

#### P-10 · None of the baselines is a decentralised protocol

🟠 **Major** · Hard to defend: **78**/100 · Paper: V

**What it is.** The paper pitches a decentralised mesh (devices relaying messages for each other) and compares it with four baselines (reference methods): static and dynamic Dijkstra and A*, which are classical route-finding methods (planners). A critic raises three problems:

1. None of the four baselines is a decentralised protocol (one where each node decides using only what it can hear). Missing from the comparison are plain flooding (every node repeats every message), ABOT's own gossip forwarding used alone (re-sending with a set probability), Meshtastic's managed flooding (Meshtastic is an open-source mesh platform), on-demand protocols such as AODV or DSR (which find routes when needed), link-quality protocols such as OLSR, B.A.T.M.A.N. or Babel, and greedy geographic routing (GPSR, which forwards each message by position).
2. All four baselines are handed a full snapshot of the network (a complete picture at one moment).
3. Greedy geographic forwarding is part of ABOT's own design, yet it is not used as a baseline.

**Why it's an issue.**

1. Without decentralised protocols, the paper cannot show how its design stacks up against methods a real mesh could use.
2. The planners see more than any real node could, so their results show a best case (an upper bound), not what a real node can achieve.
3. Leaving it out means the paper never tests one of its own forwarding rules against the other methods.

Overall, a paper about decentralisation compares itself only with centralised methods, so it has not yet shown how it stands against other decentralised designs.

**Impact on your talk.** **Have an answer ready** (Question 5). Don't claim that ABOT beats existing mesh protocols, because none was tested. Call the baselines "classical planners with a full view of the network", and say they are upper bounds (best-case comparisons), with protocol baselines still planned.

#### P-11 · Live link-quality routing already exists in mesh protocols

🟠 **Major** · Hard to defend: **75**/100 · Paper: II (gap 2)

**What it is.** The paper's second gap says that existing link-quality-aware routing acts on a static topology (a fixed network layout) or recomputes only after a failure. A critic raises three problems:

1. A per-link score of 1 divided by PDR (the share of messages that get through) is ETX, a classic measure from 2003 (expected transmission count: roughly how many tries a message needs to cross a link).
2. OLSR-ETX, B.A.T.M.A.N. and Babel (mesh-routing protocols) already update link quality continuously from hello statistics (measurements from routine "hello" messages between neighbours), which contradicts the paper's stated gap.
3. None of this work is cited.

**Why it's an issue.**

1. If the score is ETX, the measure is old, so the paper's claim to novelty has to rest on how it applies that measure.
2. The paper presents this gap as one of three reasons ABOT is needed. If existing protocols already do this, that reason falls away.
3. Leaving out well-known work makes it look as if the authors missed it, and a networking audience will notice.

Taken together, the stated gap, and so the paper's case for novelty, is easy to challenge.

**Impact on your talk.** **Have an answer ready** (Question 5). Don't say "first" or "a novel routing metric". Frame the novelty as applying live link quality to a gateway-free LoRa mesh (a long-range, low-power radio network with no fixed gateway station) under five damage levels, not as the metric itself.

⚠️ *Relies on an outside fact; check it before quoting it.*

#### P-25 · The closest prior work already has hardware results

🟠 **Major** · Hard to defend: **62**/100 · Paper: II

**What it is.** The paper says ABOT is positioned to close the post-disaster communication gap. A critic raises three problems:

1. Reference [5] already built a self-healing LoRa mesh (a long-range, low-power radio network) with no fixed gateway station, on ESP32 boards (small, programmable computer chips), and it has hardware results.
2. ABOT is simulation-only, so a critic will say the closest prior work has stronger evidence.
3. The paper never states what ABOT adds over [5] and [6].

**Why it's an issue.**

1. A system that works on real hardware has faced real radios, terrain and interference, which a simulation can only approximate.
2. So on evidence alone, ABOT looks behind the closest prior work rather than ahead of it.
3. Without a stated difference, a reader cannot tell what ABOT contributes beyond [5] and [6], so its novelty is unclear.

Taken together, the paper's contribution over the closest prior work is not stated, and a critic will press on that.

**Impact on your talk.** **Have an answer ready** (Question 5). Say what you can claim as new: live-state routing (routes chosen from current link measurements), the five-level damage benchmark (intact to extreme), and a simulator fast enough for RL (reinforcement learning, trial-and-error training). Concede openly that [5] has hardware results and ABOT doesn't yet. Hardware validation comes next.

### Q6. "SF12, a beacon every 30 s and ~30 neighbours: won't the channel jam? Is that duty-cycle legal?"

> **Your answer:** "It's a real limit, and the paper lists it. Beacons alone take about 4.4% of airtime per node, and with ~30 neighbours sharing the channel that adds up. Dense areas would need slower beacons or shorter, faster transmissions."

*Points behind this question: P-06.*

#### P-06 · Beacons alone would saturate the radio channel at this density

🔴 **Critical** · Hard to defend: **80**/100 · Paper: III; VI

**What it is.** The paper's setup uses SF12 (the slowest, longest-range setting of LoRa, a low-power radio, so each message takes a long time to send) and beacons every 30 s (short messages neighbours use to measure links), its mesh averages 30.7 neighbours per node, and it says the beacons take "roughly 4.4% channel occupancy". That works out to each node's own airtime (the time its radio is busy sending; see P-20). A critic raises three problems:

1. Beacon load: each receiver hears about 30.7 neighbours × 4.4% = about 1.35 Erlang (a unit of channel load; 1 means always busy) of beacon traffic alone, or about 2.0 with the 34-byte header (the fixed front part of each message).
2. Under the simple ALOHA model (senders transmit whenever they like, and overlapping messages collide), only about 2–7% of transmissions would get through.
3. So the channel saturates before any SOS (distress) traffic is sent, and beacon-based link monitoring can't work at this density.

**Why it's an issue.**

1. At 1.35 Erlang, the beacons alone would need more than all of the airtime around each receiver: more traffic than the channel can carry.
2. If only 2–7% of transmissions survive, most beacons are lost, and any SOS message has to compete for the same crowded channel.
3. Routing depends on that live link picture, so if beacon-based monitoring cannot work at this density, routing would lack reliable link information.

Taken together, the sum uses only the paper's own numbers, so the objection is hard to dismiss.

**Impact on your talk.** **Have an answer ready** (Question 6). Don't present beacon-based link monitoring as proven to work at this density. The paper lists duty cycle (the share of time a device may transmit) as a limitation in Section VI, so the honest line is that it's a known limit. If asked what to do, say that beacon rate or spreading factor would have to adapt at this density, and that adaptive beaconing (changing how often beacons are sent) is the planned study.

## Part 2: Watch your wording

Nobody needs a prepared answer for these 14 points. The risk is repeating one of the paper's sentences or numbers on a slide, where a sharp listener can catch it. Each rule gives the wording to avoid and what to say instead. The entries under it explain why.

### Don't open with "6.7 million deaths"

| Avoid | Say instead |
|---|---|
| "6.7 million deaths in the 1990s" [3] | No death figure; that's safest. If you want a number, use one that the triage (`ABOT-red-team-triage.md`) found in [3] itself: yearly disaster damage rose from about US$20 billion in the 1990s to about US$100 billion in 2000–10, and 97% of disaster deaths since the 1960s were in developing countries. |

*Points behind this rule: P-09.*

#### P-09 · The paper's opening death toll is probably misquoted

🟠 **Major** · Hard to defend: **80**/100 · Paper: I

**What it is.** The paper's opening statistic says disasters caused "6.7 million deaths in the 1990s alone" [3], and a critic raises three problems:

1. Summaries based on the EM-DAT disaster database (a database of recorded disasters) put 1990s natural-disaster deaths under about 0.8 million, and a typical recent year at 10–20 thousand. These are outside facts that nobody has verified yet.
2. The figure is probably misquoted. The triage has since checked [3] itself, an International Monetary Fund (IMF) working paper, and the 6.7 million figure isn't in it.
3. The statistic opens the paper, which makes it the most visible place for an error.

**Why it's an issue.**

1. If those outside figures are right, the paper's number is far too high, and anyone can look up the real one.
2. A figure that isn't in its own cited source can't be defended by pointing to that source.
3. An opening statistic is the first thing an audience sees, so a mistake there is the most visible one.

Overall, a wrong figure would be hard to defend and easy to see on an opening slide.

**Impact on your talk.** **Watch your wording.** Keep "6.7 million deaths" off the opening slide. The table's safest option is to use no death figure at all. If you want a number, the replacement figures come from [3] itself, not from the paper's own text, so name [3] when you use one.

⚠️ *Relies on an outside fact; check it before quoting it.*

### Call ABOT a protocol with four layers, not a device

| Avoid | Say instead |
|---|---|
| "ABOT, a device with a LoRa radio module"; "three functional layers" | "A protocol that runs on existing LoRa boards." "Four layers", matching Fig. 1. |

*Points behind this rule: P-50, P-39.*

#### P-50 · ABOT is called a device, but no device was built

🟡 **Minor** · Hard to defend: **30**/100 · Paper: I

**What it is.** The introduction calls ABOT "a device with a LoRa radio module" (LoRa is a long-range, low-power radio technology). A critic points out that the abstract calls it a "framework" (a structure others can build on), that Section III calls it a "protocol" (a set of rules for sending messages), and that no device was built.

**Why it's an issue.** The mismatch invites the question "can I see the device?", and it makes the paper look imprecise about what it contributes. A device is hardware, while a protocol is a set of rules, so the words describe different things. The red team calls it a wording inconsistency.

**Impact on your talk.** **Watch your wording.** Describe ABOT as "a protocol that runs on existing LoRa boards." Keep the paper's own framing, which is simulation only, and don't use "device" on slides or out loud. Use the same word on every slide, so listeners aren't left wondering what ABOT is. If "device" appears in a slide title or figure label, change it too.

#### P-39 · The text says three layers, the figure caption says four

🟡 **Minor** · Hard to defend: **80**/100 · Paper: III; Fig. 1

**What it is.** The text says ABOT has "three functional layers", but the caption of Fig. 1 (the architecture figure) reads "ABOT's Four Layer System Architecture". The updated figure gives MAC (the rules for when a radio may send) and forwarding (passing messages on to other nodes) their own layer, but the text wasn't updated. A critic calls this a plain contradiction. Both statements appear in the paper itself.

**Why it's an issue.** Anyone who compares the text with the figure sees two different answers to one question: how many layers ABOT has. Because the contradiction is plain, there is little room to argue it away. It also looks like a text left behind after the figure changed, which a listener may read as carelessness.

**Impact on your talk.** **Watch your wording.** Say "Four layers", matching Fig. 1, and never "three functional layers". On slides the fix is trivial. If asked why the two differ, say the figure was updated and the text was not.

### Give the range as "about 2 km at the default damage level"

| Avoid | Say instead |
|---|---|
| "multi-kilometre range over rubble-strewn, non-line-of-sight terrain without repeaters" | "About 2 km at the default damage level." |

*Points behind this rule: P-41.*

#### P-41 · The multi-kilometre range holds only at milder damage levels

🟡 **Minor** · Hard to defend: **60**/100 · Paper: III (physical layer)

**What it is.** The paper claims "multi-kilometre range over rubble-strewn, non-line-of-sight terrain without repeaters" (non-line-of-sight means there is no clear path between the radios, and a repeater is a relay that passes messages on). A critic checks this against the paper's own figure, where PDR (the share of messages that get through) falls to 0.5 at 2.0 km under heavy damage, the default, at 1.03 km under severe damage and at 637 m under extreme damage.

**Why it's an issue.** The claim only holds at the milder damage levels. It is made for rubble-strewn terrain, which is where the paper's own model says range shrinks as damage grows. At heavy, the default throughout the paper, the range is about 2 km, so "multi-kilometre" is a stretch even in the paper's standard setting.

**Impact on your talk.** **Watch your wording.** Give the range only for the default damage level: "About 2 km at the default damage level." Don't say "multi-kilometre" or "without repeaters". If someone asks about severe damage, the paper's own figure there is 1.03 km, so relays would be needed.

### Leave out the "33-minute routing window"

| Avoid | Say instead |
|---|---|
| Calling the 200-step cap ("roughly 33 min") "a representative post-disaster routing window" | Leave it out. Episodes actually last only a few steps, well under a minute of simulated time. |

*Points behind this rule: P-02.*

#### P-02 · Episodes last seconds, not a 33-minute window

🔴 **Critical** · Hard to defend: **85**/100 · Paper: III; RL env; V-A

**What it is.** The paper calls its 200-step episode cap, about 33 minutes, "a representative post-disaster routing window", and a critic raises five problems (an episode is one simulated run; a step is 10 simulated seconds):

1. Typical (median, the middle value) episodes last 2–4 steps, or 20–40 simulated seconds, not 33 minutes.
2. In that time there is at most one beacon round: an "I'm here" message from every node, every 30 seconds.
3. The window used to measure link quality, 50 packets (messages) or about 25 minutes, can't fill.
4. A given node (one radio device) has only about a 0.8% chance of failing in any 30 seconds. That comes to about 0.4 sudden failures per 100-node episode, since half of failures are gradual (a slow battery drain needing 300 seconds).
5. The battery never drains to the 20% threshold, below which a node's deliveries are weakened.

**Why it's an issue.**

1. A reader would picture a 33-minute window, but the results describe a run of seconds.
2. The link-quality measures come from beacons, and at most one round fits, so there is little to measure.
3. The link-quality window never completes, so the measure rests on a partly filled window.
4. Failures are too rare to test the failure handling: there is almost nothing for failures to do.
5. The battery never reaches the level that changes a delivery, so that model has no effect here.

Overall, the disaster dynamics that motivate the paper barely act.

**Impact on your talk.** **Watch your wording.** Leave the 33-minute figure out, and say that episodes last a few steps. If asked about failures or battery drain, use the backup answer below.

> **Only if asked:** *"Do failures or battery drain even matter in episodes this short?"*
>
> "Barely. Episodes last a few steps, so those effects rarely come into play. Longer, sparser scenarios are next."

### Present Fig. 2 as the channel model, and the damage levels as relative

| Avoid | Say instead |
|---|---|
| Quoting "45.5 km"; presenting the damage levels as calibrated to real measurements | Call the damage levels relative stress settings, checked for internal consistency only. |

*Points behind this rule: P-15.*

#### P-15 · The channel model's distances and damage presets look miscalibrated

🟠 **Major** · Hard to defend: **72**/100 · Paper: III; V-D

**What it is.** The paper's channel model puts the distance where PDR (the share of messages that get through) falls to 0.5 at 45.5 km under the "intact" setting, and a critic raises three problems:

1. At that distance the signal is beyond the radio horizon (where the Earth's curve blocks the signal), which is roughly 8–10 km for antennas 1–2 m above the ground.
2. The model ignores the extra loss from ground reflection over long distances.
3. A published urban model (LoRaSim) gives 156.5 dB of loss at 1 km (dB, decibels: more dB means a weaker signal), while ABOT's heavy setting, the default, gives 145.2 dB: about 11 dB more forgiving than an undamaged city in that model.

**Why it's an issue.**

1. Over 45 km, the Earth's curve blocks a ground-level handheld signal, so the "intact" figure describes a link that radios held near the ground couldn't normally make.
2. Ignoring ground reflection makes long links look stronger than they would be in practice.
3. A heavy setting that is milder than an undamaged city in a published model means the damage levels are not anchored to measured conditions.

Overall, the damage levels aren't calibrated to reality.

**Impact on your talk.** **Watch your wording.** Call the damage levels relative stress settings, not calibrated measurements, and don't quote 45.5 km. If you show Fig. 2, present it as a consistency check of the channel model, which is all the paper claims for it.

> **Only if asked:** *"45 km at 'intact'? That's past the radio horizon."*
>
> "The damage levels are relative stress settings, not calibrated to measurements, and the paper claims internal consistency only."

⚠️ *Relies on an outside fact; check it before quoting it.*

### Quote the speed-up at the grid you used

| Avoid | Say instead |
|---|---|
| A bare "7.3× faster", or "303×" | "About 4.7× faster at the 10×10 grid we used, and up to 7.3× on a small grid." 303× is with contention switched off, a setting no result uses. |

*Points behind this rule: P-32.*

#### P-32 · The speed-up headline hides its grid size and mode

🟠 **Major** · Hard to defend: **55**/100 · Paper: IV

**What it is.** The paper says the fast (timestep) simulator runs "up to 7.3× faster" than the reference (SimPy) simulator with contention on (the rule that overlapping messages can collide), and "up to 303× faster" with contention off, and that changing the failure rate moves neither figure. A critic raises three problems:

1. "Up to" gives no grid size. The red team checked the saved benchmark results: the 7.3× figure is for the smallest grid (5×5), which no experiment used. At the 10×10 grid the experiments used, they give 4.7×.
2. The 303× figure is measured with contention switched off, a mode no result uses.
3. The failure-rate check is trivially true, because failures barely happen in 20–40 second episodes.

**Why it's an issue.**

1. Readers can't tell which grid a number describes, and the highest figure comes from a grid no experiment used.
2. A mode no result uses means the 303× figure describes none of the paper's own results.
3. Because almost nothing fails in these short episodes, a changed failure rate has almost nothing to affect, so the check proves little.

Overall, the speed-up is vague but not false, so the 10×10 figure should sit next to the maximum.

**Impact on your talk.** **Watch your wording.** Quote the 10×10 figure, as the table does: "About 4.7× faster at the 10×10 grid we used, and up to 7.3× on a small grid." The 4.7× isn't printed in the paper; it comes from the committed benchmark results, so expect a listener holding the paper to know only 7.3×. If you mention 303×, say it's with contention switched off, a setting no result uses.

> **Only if asked:** *"Is 7.3× at your experiment size?"*
>
> "No. It's 4.7× at 10×10; 7.3× is on a 5×5 grid."

### Get the V-C numbers and sample sizes right

| Avoid | Say instead |
|---|---|
| "Steps-to-safe-zone are identical on all 100"; "250 episodes per preset" next to 0.267 vs 0.145 | "0.267 vs 0.145 over 100 matched episodes." Lead with ~1.8×. If you show the 43-seed 1.50×, call it a supporting check (P-29 explains why). |

*Points behind this rule: P-38, P-40.*

#### P-38 · 'Identical on all 100' wrongly suggests the planners tie

🟡 **Minor** · Hard to defend: **85**/100 · Paper: V-C, para. 1

**What it is.** Section V-C says steps to a safe zone (the rescue point a route must reach) are "identical on all 100". Read alone, that suggests the static planners (classical route-finding methods that count hops) and the dynamic planner (which weights routes by live link quality) take the same number of steps. Two sentences later the paper gives 3.23 against 2.17 steps. The sentence actually refers to a fidelity check (a test that two simulators agree): the static planners, re-run on the fast (timestep) simulator, take the same steps as on the reference (SimPy) simulator.

**Why it's an issue.** A careful reader sees a contradiction in the key results paragraph: the sentence reads as if the two planners take identical steps, yet two sentences later the paper gives 3.23 against 2.17. A listener who has read the paper may ask which number is true, and the fidelity check answers that only if you explain it. As written, the sentence can't be defended.

**Impact on your talk.** **Watch your wording.** Don't use "identical on all 100" on a slide or out loud. If the fidelity check comes up, say the static planners take the same steps on both simulators. Use the table's line for the numbers, and never let a listener hear that the static and dynamic planners take equal steps; they don't (3.23 against 2.17).

#### P-40 · The 250-episode count is attached to the wrong comparison

🟡 **Minor** · Hard to defend: **75**/100 · Paper: V-C, para. 1

**What it is.** In the same passage, the paper gives the drop in mean link PDR (a link-quality score) from 0.267 to 0.145, then attaches a sample size of 250 episodes (simulated runs) per damage level for each method. A critic says the paper has merged two analyses into one sentence. The 0.267 and 0.145 figures come from the main run of 100 episodes. The 250 belongs to the separate damage-level sweep, which covers the five damage levels (intact to extreme).

**Why it's an issue.** The headline number carries the wrong sample size, which makes anyone checking the numbers doubt them. It's like quoting one survey's sample size beside another survey's results. The honest answer is to concede the mix-up and name the run each number came from.

**Impact on your talk.** **Watch your wording.** Quote the comparison with its own sample size: "0.267 vs 0.145 over 100 matched episodes." Keep 250 for the damage-level sweep only. If someone asks, say the paper merged two analyses into one sentence, and that the main run has 100 episodes.

### Don't present 100% success or the damage sweep as robustness

| Avoid | Say instead |
|---|---|
| Reading the ~100% success, or the damage sweep, as robustness to damage; "structural damage removes the mesh's long-range shortcuts" | "Success is at ceiling, so we compare route length." |

*Points behind this rule: P-13.*

#### P-13 · Claim that damage removes long-range shortcuts is not shown

🟠 **Major** · Hard to defend: **75**/100 · Paper: V-D

**What it is.** The paper says severity hits the longer links, which is how structural damage removes the mesh's long-range shortcuts (the mesh is the network of relaying radios), and a critic raises three problems:

1. Fig. 2 puts PDR (the share of messages that get through) at 1,500 m at only 0.109 under extreme damage.
2. Yet the neighbour range (the reach that decides who counts as a neighbour) stays at 1,500 m at every damage level.
3. And all five routing methods still succeed about 100% of the time, so the long links are evidently still being used. No result shows the shortcuts being removed.

**Why it's an issue.** Each problem matters for its own reason:

1. A PDR of 0.109 means only about one message in ten gets across such a link, so if routes still use long links under extreme damage, the damage should hurt them.
2. If the neighbour range never shrinks, the long links stay in the set the routes can use, so the claim that damage removes them has nothing to rest on.
3. Routes that still succeed about 100% of the time suggest the long links are still used, and the paper has no result showing they were removed. The red team checked the code, and it confirms that a single radio jump succeeds whenever the next radio device is working, however weak the link.

Taken together, these make the claim an interpretation, not a result.

**Impact on your talk.** **Watch your wording.** Don't say that damage removes the mesh's long-range shortcuts, and don't read the ~100% success as robustness to damage. Say instead that severity degrades long links in the channel model (the simulated radio rules), and the routing task doesn't yet reflect that. Then use the table's line: "Success is at ceiling, so we compare route length." (Ceiling means close to 100%.)

### Don't oversell PPO

| Avoid | Say instead |
|---|---|
| "a lower bound"; "both run against PPO"; "the comparison is conservative with respect to the learned agent"; "the agent sees only the local observation"; "intended to replace the Dijkstra solver" | "PPO is in the same range as the classical planners on this task, but not better than the fastest ones: slightly behind them at 10×10, with no significant difference at 15×15." |

*Points behind this rule: P-12, P-42.*

#### P-12 · PPO's 'local only' view includes whole-network information

🟠 **Major** · Hard to defend: **75**/100 · Paper: III (observation; asymmetries)

**What it is.** The paper says PPO (the reinforcement-learning route chooser, trained by trial and error) sees only a local view while the classical planners (route-finding methods) see the whole network and calls PPO's result a "lower bound" (a floor: PPO should do at least this well on a fair footing), and a critic raises two problems:

1. PPO's inputs include the hop count (how many radio jumps away) to the nearest working gateway, the rescue point routes head for, and the direction to it. Both need knowledge of the whole network, which contradicts "local only".
2. The "lower bound" is asserted, never measured: the effect of the two asymmetries is never quantified.

**Why it's an issue.** Each problem matters for its own reason:

1. The paper's own list of inputs contradicts the claim that PPO sees only local information, so a careful listener can catch the mismatch. The red team checked the code, and it confirms that the hop count comes from a search across the whole network.
2. A lower bound is a claim about how much the two differences cost PPO. Because that effect is never measured, the reassurance rests on an assertion rather than a number.

Together, these leave the "lower bound" framing unsupported on its own terms.

**Impact on your talk.** **Watch your wording.** Drop "lower bound" and "sees only the local observation". Describe PPO's inputs as mostly local, plus a hint about how far away the nearest working safe zone is and in which direction. Then use the table's line about PPO being in the same range as the classical planners.

#### P-42 · Replacing the planner is an aim, not a result

🟡 **Minor** · Hard to defend: **55**/100 · Paper: I

**What it is.** The paper's introduction describes PPO (the reinforcement-learning route chooser) as an agent intended to replace the Dijkstra planner (a classical route-finding method, the one its routing layer uses). A critic says nothing in the results supports that, and PPO trails the fastest classical planners at 10×10 (the 100-node grid). It shows no significant difference from them at 15×15.

**Why it's an issue.** The introduction sets an expectation that the results don't support, and a listener who checks the 10×10 numbers will see the gap. The red team's own response is that this is the long-term aim, and that the results show it isn't there yet.

**Impact on your talk.** **Watch your wording.** Present replacing Dijkstra as a long-term aim, not a result. If someone asks whether PPO will replace the planner, say that is the goal and the current results don't show it yet; the paper itself calls the learning component exploratory. Use the table's line for the numbers.

### Don't repeat the abstract's "moderate" and "extreme network collapse" claims

| Avoid | Say instead |
|---|---|
| "Improved packet delivery performance under moderate infrastructure degradation"; "limitations of RL-based routing under extreme network collapse" | "PPO's results don't get worse as damage increases. Its one failure case shows up at every damage level, so it comes from how its choices are set up, not from the damage." |

*Points behind this rule: P-08.*

#### P-08 · The abstract's damage claims contradict the paper's own results

🟠 **Major** · Hard to defend: **80**/100 · Paper: Abstract

**What it is.** The abstract claims improved packet delivery under moderate damage and highlights limitations of RL-based routing (PPO, the reinforcement-learning route chooser) under extreme network collapse, and a critic raises two problems:

1. No result is specific to moderate damage: the dynamic Dijkstra planner (a classical route-finding method) has a PDR (its link-quality score) that stays flat from intact to heavy.
2. The limitations claim contradicts Section V-B. PPO's reward doesn't get worse with damage (the paper calls it "flat rather than degrading"). Its one bad seed block (the runs for one fixed random scenario) is already bad with no damage at all: its reward (the score PPO learns to raise) is about 16.9 from intact to heavy, then about 22.9 at severe and extreme.

**Why it's an issue.** Each problem matters for its own reason:

1. A claim the results don't show is the easiest kind for a listener to challenge, and the only planner whose PDR responds materially to damage stays flat from intact to heavy.
2. A weakness that is already there with no damage, and doesn't grow as damage increases, cannot be explained by damage, so the abstract's framing does not match the results.

Together, the abstract and the results section disagree, so the safe answer is to concede the mismatch rather than defend the wording.

**Impact on your talk.** **Watch your wording.** Don't repeat the abstract's two claims. Use the table's line instead: PPO's results don't get worse as damage increases, and its one failure case shows up at every damage level. If someone quotes the abstract, say its wording overstates the results.

### Describe the duty-cycle limit as airtime, not as an ETSI breach

| Avoid | Say instead |
|---|---|
| "well above the 1% limit ETSI EN 300 220-2 sets for this band" | "Beacon airtime is high: about 4.4% per node." ETSI EN 300 220-2 is a European standard, and the paper chose India's band. |

*Points behind this rule: P-20.*

#### P-20 · The airtime figure is miscalculated and cites the wrong rule

🟠 **Major** · Hard to defend: **68**/100 · Paper: VI (duty cycle)

**What it is.** The paper says 30-second beacons (regular "I'm here" messages) take roughly 4.4% of the channel at SF12 (LoRa's longest-range setting), well above the 1% limit that ETSI EN 300 220-2 (a European standard) sets for this band, and a critic raises three problems:

1. The arithmetic: 4.4% is 1.32 seconds of sending every 30 seconds, implying a beacon of about 20 bytes. With the paper's own 34-byte header, the beacon alone is about 6.0–6.6%, before relaying and gossip (spreading messages).
2. The jurisdiction: that standard is European, while India's 865–867 MHz band, under the LoRaWAN IN865 plan, reportedly has no duty-cycle limit (a cap on the share of time a radio can send), an unverified outside fact.
3. The wrong quantity: the paper mixes up one device's duty cycle with how busy the shared channel is.

**Why it's an issue.** Each problem matters for its own reason:

1. With the paper's own header size, the real figure is higher, so the limitation understates the problem, and anyone who knows LoRa can redo the arithmetic.
2. If India's band really has no duty-cycle limit, the paper cites a rule that doesn't apply to the band it chose.
3. One device's sending time is not how busy the shared channel is: around each receiver, all the neighbours' beacons add up (P-06 shows how far), so mixing the two understates the real congestion.

Together, these make the limitation hard to defend as written.

**Impact on your talk.** **Watch your wording.** Don't say the beacons break the 1% limit. Say the table's line: "Beacon airtime is high: about 4.4% per node." (Airtime: time spent sending.) If you mention ETSI, use the table's second sentence. If someone presses on the number, 4.4% assumes a beacon of about 20 bytes; with the 34-byte header it would be about 6.0–6.6%.

> **Only if asked:** *"ETSI doesn't apply in India."*
>
> "Right, it's a European rule. Either way, airtime at this density is the real constraint."

⚠️ *Relies on an outside fact; check it before quoting it.*

## Part 3: Safe to set aside

These 28 points are real, and a journal version would need to fix most of them. They won't hurt a 12-minute talk, though: they're too detailed for a short Q&A, already disclosed in the paper, or frozen in print. Read them once so nothing surprises you. A few have a backup line in case someone does ask.

### The paper is frozen

*Why you can set these aside:* The camera-ready paper can't change before the talk, and nobody spends Q&A time on typos or citation mix-ups. Just don't copy these mistakes onto your slides.

#### P-27 · The channel model cites a source for a different radio

🟠 **Major** · Hard to defend: **60**/100 · Paper: III (path loss)

**What it is.** The paper sets its path-loss exponent (how fast the signal weakens with distance) from "IEEE 802.15.4a CM6 measurements and post-earthquake LoRa field data [10]", and a critic raises three problems:

1. Reference [10] is the IEEE 802.15.4a final report, a channel model for UWB (ultra-wideband, a very different short-range radio), measured mostly over tens of metres.
2. The post-earthquake field data for LoRa (a long-range, low-power radio) has no citation of its own.
3. Using a UWB model at 865 MHz over kilometres needs a justification, and the paper does not give one.

**Why it's an issue.**

1. The cited report describes a different kind of radio, so it does not support the number the paper takes from it.
2. A reader cannot see which LoRa measurements the number comes from, because the only reference attached to them is the report on the other radio.
3. The exponent sets how fast the simulated signal fades with distance, so the distance results depend on it.

Together, a critic can challenge the channel model's basis and the distance results built on it.

**Impact on your talk.** **Safe to set aside.** If a slide names the channel model's source, don't write "802.15.4a CM6". The red team suggests citing the post-earthquake LoRa measurements (Ferreira et al. 2020) directly in any later version.

⚠️ *Relies on an outside fact; check it before quoting it.*

#### P-36 · The paper has harmless typos and formatting slips

🟡 **Minor** · Hard to defend: **95**/100 · Paper: Throughout

**What it is.** The paper has typos and formatting slips. Examples include a stray ", ," in the keywords, "dept. Of" in an author line, "regime. with" in the body, "(p = 0.886). which" and "(p = 0.0057,r_ rb" in the results, "amplified the damage to more damaging effects", "n_ PL" (a split symbol), "Haas et al. [9] shows", "uses Stable-Baselines3 PPO as default hyperparameters", "42 Byte", a Table II caption split across two paragraphs, and two Section VI items run together. A critic can point to each one.

**Why it's an issue.** Each slip is small, but together they can make the paper look as if it was not checked closely. The paper cannot defend them, so the response is to concede them and fix them in any later version.

**Impact on your talk.** **Safe to set aside.** If anyone mentions them, thank them. Don't copy them onto your slides.

#### P-37 · Two citations point to the wrong sources

🟡 **Minor** · Hard to defend: **85**/100 · Paper: II

**What it is.** The paper cites "Al-Hadhrami et al. [8]" for a result on power-aware routing, and cites [11] for IoT (internet-connected devices) situational awareness and the simulator gap; a critic raises two problems:

1. Reference [8] is by Olajide, a 2018 paper in PLoS ONE (a scientific journal) on power-aware routing (PARA), not Al-Hadhrami.
2. Reference [11] is a deep reinforcement learning paper (trial-and-error training) on LoRa (a long-range, low-power radio) transmission settings, yet it is cited for IoT situational awareness and for the simulator gap, and it documents neither.

**Why it's an issue.**

1. The name does not match the reference list, so a reader who checks it will find a plain factual error.
2. The citation gives no real support to either claim it sits beside. [11] isn't about IoT situational awareness, and on simulators it builds an RL environment of its own, which cuts against the gap rather than showing it (see P-24).

Both are plain factual errors, so the only defence is to concede them.

**Impact on your talk.** **Safe to set aside.** On slides, write "Olajide [8]", not "Al-Hadhrami".

#### P-49 · The paper's two figures don't show the main results

🟡 **Minor** · Hard to defend: **35**/100 · Paper: V

**What it is.** The paper has only two figures, and neither shows the main results. Figure 1 is the system's layered architecture diagram, and Figure 2 is a channel check that plots packet delivery ratio (PDR, the share of messages that get through) against distance across the five damage presets. The main results are carried by Table II alone, so a critic will say they are not shown in any figure.

**Why it's an issue.** Readers have to dig the main results out of a table, which makes them easy to miss or misread, even though the paper's text does describe them. The red team describes this as a trade-off forced by the page limit.

**Impact on your talk.** **Safe to set aside.** The slides can show the results as charts, which answers this point.

### Specialist statistics

*Why you can set these aside:* These are fair points for a statistician reviewing a later journal version, but they're too specialised for a few minutes of Q&A.

#### P-26 · Borderline 'PPO worse' verdict and strong 'indistinguishable' wording

🟠 **Major** · Hard to defend: **60**/100 · Paper: V-A (Table II)

**What it is.** Table II says PPO (a reinforcement-learning route chooser, trained by trial and error) does worse than three route-finding planners (such as Dijkstra and A*) at 10×10, and shows no difference at 15×15; a critic raises three problems:

1. At 10×10 the three planners give identical results (Table II reports them in one row), so one comparison is counted three times when the paper corrects its p-values for running several tests.
2. The 'PPO worse' verdict rests on a corrected p-value of 0.047 (roughly, how likely a gap this big is by chance), just under the usual 0.05 cut-off.
3. At 15×15 the effect points the same way, with r_rb (how large the gap is, from −1 to +1) of about +0.137, yet the text says PPO is 'indistinguishable' from the three fastest planners.

**Why it's an issue.**

1. The correction depends on how many separate tests were run. Counting one comparison three times distorts it, which a statistician would spot.
2. A result just under the usual cut-off is borderline, so a critic can say the verdict is not secure.
3. The effect at 15×15 points the same way as at 10×10, so 'indistinguishable' claims more than the numbers show, and 'no significant difference' is the accurate phrase.

Together these make the 10×10 verdict look borderline and the 15×15 wording look too strong.

**Impact on your talk.** **Safe to set aside.** If you mention 15×15, say "no significant difference", not "indistinguishable" or "the same".

#### P-29 · The 43-seed result was chosen after seeing the data

🟠 **Major** · Hard to defend: **58**/100 · Paper: V-C

**What it is.** To isolate replanning (changing a route mid-run), the paper reports a 1.50× separation between its two Dijkstra planners (route-finding methods) on 43 of its 100 seeds (fixed scenarios that can be replayed exactly), those where both plan the same first route; a critic raises two problems:

1. The 43-seed subset was chosen after seeing the data (post hoc, meaning picked after the fact).
2. Its p-value of 0.0057 (roughly, how likely a gap this big is by chance) is not corrected for that choice.

**Why it's an issue.**

1. Picking a subset after seeing the results is a standard objection, because it can make a result look stronger than it is.
2. A p-value that ignores the choice cannot be read at face value, so the best response is to label the result as an exploratory isolation of replanning.

So the 43-seed result belongs with the supporting evidence, not the headline claims.

**Impact on your talk.** **Safe to set aside.** Keep the 43-seed result off the main slides. If you show it, call it a supporting check.

#### P-34 · The comparison tests ignore that scenarios are paired

🟠 **Major** · Hard to defend: **50**/100 · Paper: V

**What it is.** Every agent runs on the same scenarios, with the same start point and the same failures, so the results come in matched pairs. The paper reports "rank-based tests" without naming them. The red team checked the code: they are Mann–Whitney U tests, which treat two sets of results as unrelated and so ignore that pairing. A paired test, such as the Wilcoxon signed-rank or sign test (tests built for matched pairs), would fit the design better.

**Why it's an issue.** The test does not match the design, and a critic will say so. The red team also judges the test probably conservative (cautious, so less likely to find a difference), which means the conclusions likely still hold. The red team's suggested reply is that paired tests would be added in a later version.

**Impact on your talk.** **Safe to set aside.** Nothing to change on slides.

#### P-46 · The headline ratios have no precision ranges

🟡 **Minor** · Hard to defend: **45**/100 · Paper: V-C

**What it is.** The paper reports a separation of about 1.8–1.9× between its dynamic and static Dijkstra planners (route-finding methods) at intact through heavy damage, and a critic raises two problems:

1. The 1.8–1.9× ratios come without confidence intervals (ranges showing how precise a number is).
2. The dynamic planner's score (its mean link PDR, a link-quality score) alone ranges from 0.264 to 0.294 depending on the hash seed (a setting that decides how ties between equally good routes are broken).

**Why it's an issue.**

1. Without intervals, a reader cannot tell how precise a ratio is, so a single figure looks more exact than the evidence supports.
2. The ratio is built on that score, so it is open to the same tie-breaking effect, which the paper discloses but does not turn into a range.

Together, the figure should be quoted as an approximate value, not a precise one.

**Impact on your talk.** **Safe to set aside.** Say "about 1.8×" rather than a figure with two decimal places.

#### P-52 · The reward–steps link is built in, not discovered

🟡 **Minor** · Hard to defend: **25**/100 · Paper: V

**What it is.** The paper reports that reward almost perfectly tracks the number of steps to a safe zone (Pearson r, a measure of how closely two numbers move together, of −0.987 to −0.993). It uses this to justify comparing agents on steps. A critic would point out that this is automatic: the reward is roughly 100 minus the number of steps, plus small extras.

**Why it's an issue.** Presenting something that is true by design as if it were a finding can look like padding. Little rides on it, though: the paper only uses it to justify its choice of metric.

**Impact on your talk.** **Safe to set aside.** If you need to justify comparing steps, say: "Reward is mostly set by the number of steps, so we compare steps directly."

### Protocol and radio details

*Why you can set these aside:* A 12-minute talk won't reach this level of detail. They only matter if these details appear on a slide, so keep packet formats and channel-access details off the main slides.

#### P-16 · The packet sizes don't add up

🟠 **Major** · Hard to defend: **70**/100 · Paper: III (packet format; gossip budget)

**What it is.** The paper says each message has a 34-byte header (its opening data), and that the 42-byte gossip payload (the data a gossip message carries) fits within the 51-byte MTU (maximum transmission unit, the largest message allowed); a critic raises two problems:

1. A 34-byte header plus a 42-byte payload comes to 76 bytes, which is more than the 51-byte limit the paper cites.
2. The header also carries an RSSI field (received signal strength, a reading the receiver takes itself), and there is no reason for a sender to transmit a reading of that kind.

The red team checked the code, which confirms that the 34-byte layout is simulator bookkeeping.

**Why it's an issue.**

1. The paper's own figures don't add up, and any reader can check the sum.
2. Sending a reading that only the receiver can take uses room in a message whose size the paper's own figures already overrun (see problem 1).

Overall, the size check relies on a header that the red team identifies as simulator bookkeeping, and the on-air header still needs specifying.

**Impact on your talk.** **Safe to set aside.** Keep packet formats off your slides. If asked, say the 34-byte layout is simulator bookkeeping, and the real on-air header is compact but still needs specifying.

#### P-21 · The channel model assumes timing the design doesn't describe

🟠 **Major** · Hard to defend: **68**/100 · Paper: III (contention)

**What it is.** The paper says channel contention uses slotted ALOHA (nodes send only at the start of shared time slots), with capture (the stronger of two overlapping messages can survive) [2]; a critic raises two problems:

1. Slotted ALOHA needs every node to share one clock, and the cited source [2] gets that clock from a gateway (a fixed base station in LoRaWAN, a widely used LoRa standard). ABOT has no gateway and describes no time sync.
2. Capture is also decided without a timing condition (preamble lock, where a receiver locks onto the start of a message).

**Why it's an issue.**

1. The method's precondition, a shared clock, clashes with a design that has no gateway to supply one, so the model relies on timing the design doesn't describe.
2. Without that timing condition, the rule for which of two overlapping messages survives is a simplification of what real receivers do.

Overall, the collision model should be described as a simulation approximation, not as a worked-out design for real radios.

**Impact on your talk.** **Safe to set aside.** If asked, say it is a simplified model of collisions for simulation, not a design for real radios.

⚠️ *Relies on an outside fact; check it before quoting it.*

#### P-33 · Missed beacons can't be counted without sequence numbers

🟠 **Major** · Hard to defend: **55**/100 · Paper: III

**What it is.** The paper says each node estimates PDR (the share of messages that get through) from arrival statistics over 50 packets, and that a beacon (a short, regular broadcast) carries only the sender's ID; a critic raises two problems:

1. A beacon carries no sequence number (a running count attached to each message), so a receiver can't count the beacons it missed.
2. The only workaround, assuming a fixed schedule, breaks when beacon timing is jittered (small, unpredictable delays).

**Why it's an issue.**

1. Without a count, a receiver can't tell when beacons are missing, so its PDR figure rests on an assumption rather than on what it counted.
2. Assuming a fixed schedule is the only way round this, and any random variation in beacon timing breaks it. The partial defence: a receiver can still expect about one beacon every 30 seconds, though that is an expectation, not a count.

Overall, routing in the paper depends on these PDR figures, so a reader may ask how they are measured.

**Impact on your talk.** **Safe to set aside.** Describe link monitoring as a design, and nothing on your slides needs changing. If asked, say receivers can expect beacons every 30 seconds, and sequence numbers would make the count more reliable.

#### P-35 · Nodes are assumed static, yet the paper mentions movement

🟠 **Major** · Hard to defend: **50**/100 · Paper: III

**What it is.** The paper says that as nodes fail or move out of range, the mesh reconfigures around them; a critic raises two problems:

1. No movement, fading (signal strength changing over time) or change in the channel over time is described or tested, and each node's neighbours (the nodes it can reach directly) are fixed by a 1,500 m range at every damage level.
2. The paper's words "move out of range" contradict that, because the nodes are assumed to be static.

**Why it's an issue.**

1. A static model can't show how a mesh copes with movement or fading, so a reader may assume the study covers conditions it never tests.
2. Simplifying to static nodes is acceptable, but the words "move out of range" describe behaviour the study never tests, so the paper's wording goes further than its study.

Overall, the study should be presented as a static-node simulation, with mobility as future work.

**Impact on your talk.** **Safe to set aside.** Say the nodes are static in this study, and don't say they move. Mobility is future work.

#### P-43 · The 51-byte size limit is borrowed from LoRaWAN

🟡 **Minor** · Hard to defend: **50**/100 · Paper: III (gossip budget)

**What it is.** The paper sets its largest message at 51 bytes, the SF12 DR0 limit (SF12 is one of LoRa's radio settings), and sizes its gossip payload (the data a gossip message carries) to fit within it; a critic raises two problems:

1. The 51-byte limit is a LoRaWAN rule (LoRaWAN is a widely used standard for LoRa, a long-range, low-power radio), set by DR0, LoRaWAN's slowest data-rate setting. Raw LoRa, without LoRaWAN's rules, allows 255 bytes.
2. The paper describes its design as "Unlike conventional LoRaWAN systems", so borrowing a LoRaWAN limit sits oddly with that framing.

**Why it's an issue.**

1. A LoRa design, where raw LoRa allows 255 bytes, takes the smaller LoRaWAN figure, and a reader may ask why. The answer offered is a conservative budget.
2. A reader who knows LoRaWAN will notice that the design borrows one of its rules, despite the contrast the paper draws.

Overall, the limit is a defensible conservative choice, but it is borrowed from a protocol the paper sets itself against.

**Impact on your talk.** **Safe to set aside.** If asked, say the limit is a conservative budget that keeps messages compatible with LoRaWAN-class radios (radios built to LoRaWAN's rules).

#### P-44 · The 25% saving restates the chosen probability

🟡 **Minor** · Hard to defend: **45**/100 · Paper: III (forwarding)

**What it is.** The paper says forwarding with p = 0.75 (each node repeats 75% of messages) saves roughly 25% of a full flood's transmissions (every node repeating every message); a critic raises three problems:

1. The claim of roughly 25% savings restates p = 0.75 rather than measuring anything.
2. p and K (the duplicate count that stops a node repeating) were never tested at other values.
3. Haas et al.'s thresholds (the levels where messages reliably spread) come from far sparser networks than ABOT's, which has about 30 neighbours per node.

**Why it's an issue.**

1. The 25% figure follows from the setting itself, so it isn't evidence of a saving, even though the reasoning behind p is sensible.
2. Without trying other values, the paper can show only that p was chosen with margin, not that p and K are the right values.
3. The paper cites those thresholds for "moderately dense" networks and says p = 0.75 leaves margin for sparser ones. But the thresholds come from networks with far fewer neighbours than ABOT's ~30, so it isn't shown that they carry over to ABOT's dense mesh.

Overall, p = 0.75 is a reasonable setting that should be described as chosen with margin, not as a measured saving.

**Impact on your talk.** **Safe to set aside.** If you mention p = 0.75, present it as a setting chosen with margin, not a measured saving.

#### P-48 · The paper doesn't mention half-duplex or listen-before-talk

🟡 **Minor** · Hard to defend: **40**/100 · Paper: III

**What it is.** The paper describes channel contention, capture and forwarding in some detail, and a critic raises two problems:

1. Half-duplex operation (a radio that can't send and listen at the same time) isn't mentioned.
2. Listen-before-talk (checking that the channel is free before sending; Meshtastic does this with LoRa's channel activity detection, CAD) isn't mentioned.

**Why it's an issue.**

1. A reader who knows radios will ask whether a node can send and receive at once, and the paper gives no answer.
2. Listen-before-talk is the check that stops a node transmitting into a busy channel, and the paper doesn't say how a node avoids doing that.

Overall, both are omissions rather than contradictions, and the features are not modelled yet.

**Impact on your talk.** **Safe to set aside.** If asked, say these aren't modelled yet, and that listen-before-talk is planned.

### Gaps in the literature review

*Why you can set these aside:* Missing citations matter for a journal version. In Q&A, the broader "how does this compare?" question (Q5) covers them.

#### P-24 · Existing tools contradict the claimed research gap

🟠 **Major** · Hard to defend: **65**/100 · Paper: II (gap 1)

**What it is.** The paper says simulators for LoRa (a long-range, low-power radio) offer no agent interface fast enough for reinforcement learning (RL, trial-and-error training), citing [11]; a critic raises three problems:

1. ns3-gym connects the ns-3 simulator (a widely used network simulator), which has a LoRaWAN module (a LoRa network standard), to the standard RL interface.
2. FLoRa, LoRaSim and Meshtastic's Meshtasticator already exist.
3. [11], the source cited for the gap, itself builds a deep reinforcement learning environment for LoRa.

**Why it's an issue.**

1. If a standard RL interface already runs on a widely used simulator, the gap as stated is hard to defend.
2. The paper says LoRa simulators in general lack this interface and doesn't name these tools, so each one counts against the claim unless the paper explains how it differs.
3. Citing, as evidence of the gap, a source that builds exactly such an environment undermines the claim.

Overall, the gap is weaker than the paper states, because existing tools, the cited source among them, already address this area.

**Impact on your talk.** **Safe to set aside.** Say ABOT offers a fast, mesh-specific environment rather than that no simulator exists. The red team's suggested answer is that the other tools target LoRaWAN or single-hop (one radio jump) links.

⚠️ *Relies on an outside fact; check it before quoting it.*

#### P-47 · The related work omits reinforcement-learning routing

🟡 **Minor** · Hard to defend: **40**/100 · Paper: II

**What it is.** The paper's related-work section does discuss other routing approaches, such as AI-optimised routing [7] and power-aware routing [8], but it cites no reinforcement-learning (RL, trial-and-error training) routing work. A critic points out that this literature is missing, from Q-routing (a 1994 RL routing method) onward, including deep reinforcement learning routing in wireless sensor networks, flying drone networks (FANETs) and LoRa (a long-range, low-power radio).

**Why it's an issue.** It is an omission, and one that is easily added. Without that literature, a reader can't see how ABOT's RL part compares with earlier RL routing work, so it's hard to judge what is new. Overall, this is a gap in the related-work section that a later version can fill.

**Impact on your talk.** **Safe to set aside.** If asked, say the related-work section was space-limited and that RL-routing work will be added.

⚠️ *Relies on an outside fact; check it before quoting it.*

### Already scoped, or easy to defend

*Why you can set these aside:* The paper already frames these carefully, or there's a short, convincing answer.

#### P-30 · Clustered failures are motivated but never tested

🟠 **Major** · Hard to defend: **55**/100 · Paper: I; III

**What it is.** The introduction says a learned policy may better account for non-stationary (changing over time), spatially correlated (clustered in one area) failure patterns of post-disaster meshes. The paper's failure model includes a burst mode, a collapse within one grid cell of an epicentre, and a critic points out that burst (spatially clustered) failures are implemented but never evaluated, because every experiment uses the mixed mode (a blend of sudden and gradual node failures).

**Why it's an issue.** The motivation leans on spatially correlated failures, yet that case is never tested. The paper states this as motivation rather than as a result, which keeps the claim defensible, but a reader may assume the experiments covered clustered failures, and that assumption would be wrong.

**Impact on your talk.** **Safe to set aside.** Don't claim the experiments tested clustered failures. Their evaluation is future work.

#### P-51 · Every route ends at one of two fixed safe zones

🟡 **Minor** · Hard to defend: **30**/100 · Paper: Abstract; V

**What it is.** The abstract says ABOT operates without centralized gateways, and a critic raises two problems:

1. Every episode (one simulated run) routes to one of two safe zones (the rescue points a route must reach). The red team checked the code: they are always the same two corner nodes.
2. The learned agent's inputs (PPO, the trial-and-error trained route chooser) use the "nearest alive gateway".

**Why it's an issue.**

1. Two fixed destinations mean the evaluation is built around two points, which sits awkwardly with a design meant to do without central points.
2. Giving the agent a gateway input reminds a reader of the central point the design claims to do without.

Overall, the evaluation is built around fixed destinations, which sits awkwardly with "operates without centralized gateways", but the reply is defensible because the safe zones stand for rescue teams' nodes, not infrastructure gateways.

**Impact on your talk.** **Safe to set aside.** If asked, say the safe zones stand for rescue teams' nodes, not infrastructure gateways.

### RL internals

*Why you can set these aside:* These are too detailed for a short Q&A. Backup lines cover the two that could come up: which trained model the results use, and the livelock.

#### P-14 · The paper doesn't say which trained model its results use

🟠 **Major** · Hard to defend: **72**/100 · Paper: V-A; VI

**What it is.** The paper reports three training runs of PPO (the trial-and-error trained route chooser), with explained variance (how well PPO's reward predictor fits; 1 is perfect, 0 or below is no better than guessing) of −0.67, 0.18 and 0.71, and says value estimation "clearly hasn't converged for at least one of them" (converged: settled on stable predictions). The red team raises three problems:

1. One run's critic is plainly unsettled: an explained variance of −0.67 is worse than always guessing the average.
2. The paper doesn't say which run's policy produced Table II. The red team's code check confirms it is the run that scored −0.67.
3. The p-values (the chance of a gap this size by luck) treat 100 simulated runs (episodes) of one trained model as samples of PPO, so variation between training runs isn't reflected.

**Why it's an issue.**

1. A predictor that does worse than guessing suggests that training run hadn't settled, which raises doubt about any policy it produced.
2. Without that detail, a reader can't judge the results. They come from the least settled of the three runs, which a reader would want to know.
3. The tests can't show whether the gap would hold for another training run, since that variation is never measured.

Together, the headline results rest on one unnamed trained model, and their robustness is never measured.

**Impact on your talk.** **Safe to set aside.** If asked, give the answer below. It states a fact the paper leaves out.

> **Only if asked:** *"Which of the three PPO models is in the results?"*
>
> "One trained model, seed 0. The 15×15 numbers use that same model, without retraining."

#### P-23 · The livelock claim rests on one repeated scenario

🟠 **Major** · Hard to defend: **65**/100 · Paper: V-B

**What it is.** The paper reports that PPO (the trial-and-error trained route chooser) succeeds in 0.996 of its 250 simulated runs at each damage level, and attributes the shortfall to a livelock (the agent keeps repeating a useless move without making progress). The red team raises two problems:

1. 0.996 over 250 runs is one failure at each level, and it comes from the same seed (a fixed random scenario that can be replayed exactly) every time: one scenario replayed five times, not a pattern.
2. The cause, the livelock, is stated as fact, without step-by-step evidence.

**Why it's an issue.**

1. Five damage levels of one scenario make a single failure look like five separate events, which overstates how much evidence there is.
2. Without step-by-step evidence, the cause can't be checked. The red team found that the saved results don't keep the per-run record that would show it.

Together, the claim rests on one scenario, and its cause is stated without the record that would back it up.

**Impact on your talk.** **Safe to set aside.** If it comes up, say it's one failure case, reported for transparency, not a trend. Then use the livelock answer below.

> **Only if asked:** *"What was the livelock?"*
>
> "In one test scenario the policy kept picking a neighbour that had died. That one scenario recurs at every damage level. Hiding dead neighbours from the choice, known as action masking, fixes it."

#### P-28 · PPO's eight choices depend on how the nodes are numbered

🟠 **Major** · Hard to defend: **60**/100 · Paper: III (action space)

**What it is.** The paper says PPO (the trial-and-error trained route chooser) picks from eight fixed options, the neighbours (nearby devices) sorted by ID number. The red team raises two problems:

1. Which eight neighbours PPO can choose depends on how the nodes happen to be numbered, not on link quality or direction.
2. Dead neighbours stay choosable, which leads to the livelock (the agent keeps repeating a useless move). The design neither hides dead choices nor picks neighbours by geometry, and a masked or geometry-based set of choices is the standard approach.

**Why it's an issue.**

1. Numbering is arbitrary: number the same network differently and PPO's options change, though nothing about the radio links has changed. That makes the design hard to motivate.
2. Choices that can't be used stay on the list, so the agent can keep picking a dead neighbour and get stuck; masking, which hides invalid choices, is the usual fix.

Together, these make the eight-option design hard to justify.

**Impact on your talk.** **Safe to set aside.** Keep the list of eight choices off the main slides. If asked, say the fixed list of eight was a simplification, and masking invalid choices is the fix.

#### P-31 · The +5 reward pays for traffic the agent doesn't control

🟠 **Major** · Hard to defend: **55**/100 · Paper: III (reward)

**What it is.** The paper's reward includes +5 for each new SOS (a distress message) delivered. A critic says that bonus pays for something the agent doesn't control: the agent's moves don't deliver SOS messages, because the simulator creates and spreads them. The red team checked the code and the results, and the bonus fired in 100 of 100 simulated runs on the fast (timestep) simulator.

**Why it's an issue.** A reward the agent can't influence teaches it nothing, since the bonus arrives whatever the agent does. Describing it as a shaping term (an extra reward meant to nudge learning), as the paper does, misleads readers about what the agent learns from.

**Impact on your talk.** **Safe to set aside.** Keep the reward table off the main slides. If asked, the red team's suggested answer is that it acts as a background network-health signal and will be removed or tied to the agent's own node.

#### P-45 · The livelock may be blamed on the wrong cause

🟡 **Minor** · Hard to defend: **45**/100 · Paper: V-B; VI

**What it is.** The paper blames the livelock (the agent repeating a useless move) on cutting the choice list to eight, which it calls action-space truncation. A critic says the cause is the environment's design: dead neighbours (devices that have failed) stay pickable, and an invalid choice changes nothing, so the agent repeats itself.

**Why it's an issue.** This is mostly a matter of attribution, but it matters for the fix. A critic says action masking, which hides invalid choices, is what stops the loop, whereas the paper's explanation points at the length of the list.

**Impact on your talk.** **Safe to set aside.** If you explain the livelock, blame "dead neighbours stay pickable", not "only 8 slots". If pressed, it's fair to say masking invalid choices is the fix.

> **Only if asked:** *"What was the livelock?"*
>
> "In one test scenario the policy kept picking a neighbour that had died. That one scenario recurs at every damage level. Hiding dead neighbours from the choice, known as action masking, fixes it."

### Simulator and ablation details

*Why you can set these aside:* The paper already discloses these, and they only matter if you present them.

#### P-17 · The simulator match on alive nodes is nearly guaranteed

🟠 **Major** · Hard to defend: **70**/100 · Paper: IV

**What it is.** The paper uses KS tests (a test of whether two sets of numbers look alike) to compare its two simulators, finds they agree on alive-node counts (p = 0.98; a small p would signal a real gap) but not on PDR (the share of messages that get through) or delivery counts (p < 10⁻³), and says the agent trains against liveness (which nodes are alive). The red team raises two problems:

1. Matching on alive-node counts is nearly guaranteed, because both simulators run the same failure model and failures don't depend on traffic. So the match validates nothing about networking.
2. The agent's inputs are built from PDR features, which are exactly what the tests show isn't equivalent.

**Why it's an issue.**

1. A match that would almost always occur can't count as evidence that the simulators agree on networking, because the check says nothing about the network simulation itself.
2. PDR-based training results would be specific to one simulator, since the paper's equivalence claim covers only liveness.

Together, the equivalence claim covers liveness, while the inputs the agent actually learns from don't carry over between the simulators.

**Impact on your talk.** **Safe to set aside.** If you mention the comparison, say the simulators agree on which nodes are alive, not on traffic.

#### P-18 · The gossip test was bound to find no difference

🟠 **Major** · Hard to defend: **70**/100 · Paper: IV-A

**What it is.** The paper's gossip ablation (runs with and without nodes sharing their forecasts of future reward) finds no difference between the groups, and presents it as a test of "Q-value gossip". The red team raises three problems:

1. The step that merges shared forecasts isn't connected, and nothing in the policy reads them, so a null result (no difference) was guaranteed. The paper itself says only "gossip transport and its airtime cost" were exercised. The red team's code check goes further: at evaluation, no gossip is sent at all.
2. Calling it an ablation of "Q-value gossip" overstates what was tested.
3. "Per-node V(s)" (the value estimate for a state) has no clear meaning, because V depends on elapsed time and PDR (the share of messages that get through), yet it is averaged per node.

**Why it's an issue.**

1. A test in which nothing reads the shared forecasts can only show what sending gossip costs, so the "no difference" result was built in.
2. The label suggests the test checked whether gossip helps, but at most it checked transport, so readers could mistake the result for evidence on gossip's value.
3. A figure with no single clear meaning can't carry a claim about gossip.

Together, the label and the averaged figure claim more than the test can show.

**Impact on your talk.** **Safe to set aside.** If gossip comes up, say "Gossip made no difference; its merge step isn't connected yet." Don't present it as a test of gossip's value, and don't say the enabled arm paid gossip's airtime: the red team found that no gossip is sent at evaluation.

#### P-19 · The replanning explanation contradicts itself

🟠 **Major** · Hard to defend: **70**/100 · Paper: V-C, para. 3

**What it is.** The paper says both dynamic planners (route-finding methods) start from an empty network snapshot (every link weighted equally), so any separation from their static counterparts comes from replanning (recalculating a route) alone. The same paragraph then restricts the analysis to the 43 of 100 seeds (fixed random scenarios) where first routes match, and a critic reads this as conceding that in the other 57 the routes differ because of how ties between equally good routes are broken.

**Why it's an issue.** The paragraph contradicts itself, which undermines the claim it is trying to make: it gives replanning as the sole cause, then, on the critic's reading, concedes another cause in 57 of the 100 seeds.

**Impact on your talk.** **Safe to set aside.** Don't say "any separation comes from replanning alone." If asked, the red team's suggested answer is that the full-sample ratio includes tie-breaking effects, and the 43-seed subset isolates replanning.

## Your slide checklist

Run through this list once your slides are drafted. Each line names the points behind it.

**Opening and design**

- [ ] No "6.7 million deaths" on the opening slide. No death figure at all is safest (P-09).
- [ ] ABOT is "a protocol that runs on existing LoRa boards", with **four** layers, as in Fig. 1 (P-50, P-39).
- [ ] Range is "about 2 km at the default damage level", not "multi-kilometre without repeaters" (P-41).
- [ ] The planners are described as having a full view of the network, as a best case (P-03).
- [ ] No packet formats, reward table, 43-seed analysis or gossip encoding on the main slides (P-16, P-31, P-29, P-18).

**Simulator and channel**

- [ ] The damage levels are called relative stress settings, not calibrated measurements, and "45.5 km" isn't quoted. Fig. 2, if shown, is a consistency check of the channel model (P-15).
- [ ] Speed is "about 4.7× faster at the 10×10 grid we used, and up to 7.3× on a small grid". No "303×" unless you add that contention was switched off (P-32).
- [ ] No "33-minute routing window" (P-02).

**Results**

- [ ] The main result says that live link-quality scores change the routes, giving about 1.8× higher scores. Never "better delivery" or "the delivery gain" (P-01, P-07).
- [ ] Every "PDR" on a slide is labelled with what it measures (P-04, P-22).
- [ ] "0.267 vs 0.145 over 100 matched episodes". If the 43-seed 1.50× appears at all, it's called a supporting check (P-38, P-40, P-29).
- [ ] The ~100% success is presented as "at ceiling, so we compare route length", not as robustness to damage (P-05, P-13).
- [ ] PPO is "in the same range as the classical planners on this task, but not better than the fastest ones". No "lower bound" and no "replace Dijkstra" (P-12, P-42).
- [ ] At 15×15, "no significant difference", not "indistinguishable" (P-26).
- [ ] PPO's results don't get worse as damage increases. Its one failure case shows up at every damage level, so it comes from how its choices are set up, not from the damage (P-08, P-23, P-45).

**Limitations and next steps**

- [ ] Duty cycle is "beacon airtime is high: about 4.4% per node", not "above the 1% ETSI limit" (P-20, P-06).
- [ ] No claim to beat Meshtastic or established mesh routing. The novelty is framed as live link quality in a gateway-free LoRa mesh across five damage levels (P-10, P-11, P-25).
- [ ] Optional, but worth it: a "Next steps" slide listing hops that can fail on weak links, end-to-end SOS delivery and delay, random safe-zone placement with dead neighbours hidden from the agent, and hardware tests on Meshtastic boards. It answers Questions 1–3 before anyone asks them (P-05, P-01, P-03).

## What still stands

The red team also spelled out what survives its attack (§14 of `ABOT-red-team.md`). It's worth remembering on stage:

- **The paper is unusually candid.** It already says that validation is simulation only, that PPO isn't better than the fastest planners, that the gossip merge step isn't connected, that the two simulators disagree on PDR, that one planner's scores shift with how ties are broken, that the A* comparison showed no effect, and that the critic didn't converge. (Two of the three reviewers ticked "best paper" on the version they saw.)
- **The infrastructure is real.** The two simulators, the RL training environment, the statistics pipeline and an audit trail that re-derives the numbers all exist.
- **A narrow claim holds.** In simulation, a planner that re-plans on a live link-quality score picks routes through nodes that score higher on it. That shows the pipeline works end to end. It doesn't yet show better delivery.
- **The livelock diagnosis points the right way.** Dead neighbours shouldn't stay pickable, and action masking (hiding invalid choices from the agent) is the right fix.

**The safest way to state each headline** (adapted from the red team's "narrowest defensible version"):

| Headline | Safest version |
|---|---|
| Live link state | In simulation, a planner that re-plans on a live link-quality score reaches nodes with higher scores. Delivery itself wasn't measured. |
| PPO | A PPO agent trained in this environment reaches a safe zone in a similar number of hops to the planners. The task needs to be harder before the comparison means much. |
| Fast simulator | About 4.7× faster than the reference (SimPy) simulator at the 10×10 grid used. The two simulators agree on which nodes are alive, not on traffic. |
| Gossip | The sending side is built. Whether gossip helps hasn't been tested yet. |

## Glossary

Plain-English meanings of the technical terms used in this guide, in alphabetical order.

| Term | What it means |
|---|---|
| **A\*** | A faster version of Dijkstra's shortest-path method; it uses a distance estimate (a "heuristic") to search in the right direction first. |
| **Ablation** | An experiment that switches one part off to see whether it matters. |
| **Action masking** | Hiding invalid choices (such as dead neighbours) so the agent can't pick them. |
| **Action space** | The set of choices the agent has at each step. In ABOT there are 8 slots, each pointing to a neighbour in a fixed list sorted by ID number. |
| **Agent / policy** | The trained decision-maker (here, PPO). The policy is its rule for turning what it sees into a choice. |
| **Airtime / duty cycle** | The share of time a radio spends transmitting. Some regions cap it by law; Europe's ETSI rule sets 1% for this kind of band. |
| **ALOHA / slotted ALOHA** | The simplest way to share a radio channel: send whenever you have something, and overlapping messages collide. In slotted ALOHA, senders start only at the beginning of shared time slots, which needs synchronised clocks. |
| **AODV / DSR** | Routing protocols for ad-hoc networks that look for a route only when a message needs one. |
| **At ceiling** | When a score can't go any higher (here, success near 100%), so it can no longer tell methods apart. |
| **Baseline** | A standard method you compare your own method against. |
| **Beacon** | A short "I'm here" message that every ABOT node broadcasts every 30 seconds, so neighbours can judge how good the link is. |
| **Capture effect** | When two messages overlap, the receiver can still read the much stronger one; in the paper, it must be at least 6 dB stronger than the other. |
| **Confidence interval / bootstrap** | A range showing how precise a number is. The bootstrap estimates this by recomputing the number on many randomly re-drawn copies of the data. |
| **Contention** | Nodes competing for the same radio channel, so messages sent at the same time can collide. |
| **Critic / explained variance** | PPO's critic is the part that predicts future reward. Explained variance scores those predictions: 1 is perfect; 0 or below is no better than always guessing the average. |
| **Damage levels (presets)** | The five settings in the paper (intact, moderate, heavy, severe, extreme) that make radio signals fade faster with distance, to mimic more destruction. "Heavy" is the default. |
| **dB (decibel)** | A unit for signal strength or loss, on a scale where every 10 dB is a factor of ten. More loss in dB means a weaker signal. |
| **Decentralised** | No central controller; every node decides for itself using what it can hear. |
| **Dijkstra (static / dynamic)** | The classic method for finding the cheapest route through a network. Static Dijkstra counts hops; dynamic Dijkstra weights links by live link quality and re-plans when a link ahead dies or weakens. |
| **Episode** | One simulated run, from a start node until it reaches a safe zone or time runs out. |
| **Erlang** | A unit of channel load. 1 Erlang is enough traffic to keep a channel busy all the time; above 1, there is more traffic than the channel can carry. |
| **ETSI EN 300 220-2** | A European standard for short-range radio devices, including duty-cycle limits. It doesn't govern India's 865–867 MHz band. |
| **ETX (expected transmission count)** | A classic link-quality measure from 2003: roughly how many tries a message needs to cross a link, about 1 divided by the link's PDR (the share of messages that get through). |
| **Fast simulator / reference simulator** | The paper's two simulators. The fast (timestep) simulator produced the results; the slower reference (SimPy) simulator was used to check it. |
| **Flooding** | Every node rebroadcasts every new message it hears. |
| **Gateway** | In a standard LoRa network (LoRaWAN), the base station that collects messages from devices and connects them to the internet. ABOT is designed to work without one. |
| **Gossip (Gossip3)** | Forwarding where each node rebroadcasts a message with some probability (0.75 in ABOT), and stops rebroadcasting once it has heard 3 copies. |
| **Greedy geographic routing (GPSR)** | Passing each message to the neighbour closest to its destination, using the nodes' positions. |
| **Half-duplex** | A radio that can't send and receive at the same time. |
| **Hash seed** | A hidden setting of the programming language (Python) that, in ABOT's code, decides how ties between equally good routes are broken. Changing it shifts one planner's scores slightly. |
| **Header / MTU** | The header is the addressing and control part of a message (34 bytes in the paper); the MTU is the largest message allowed (51 bytes in the paper). |
| **Holm correction** | A way of adjusting p-values when several statistical tests are run at once, so that chance findings don't slip through. |
| **Hop** | One radio jump from a node to a neighbour. |
| **Jitter** | A small random delay added to when a message is sent, so that nodes don't all transmit at the same moment. |
| **KS test (Kolmogorov–Smirnov)** | A statistical test of whether two sets of numbers look as if they come from the same source. The paper uses it to compare its two simulators. |
| **Listen-before-talk (CAD)** | Checking that the channel is free before sending. LoRa radios can do this with Channel Activity Detection (CAD). |
| **Livelock** | The agent keeps repeating a useless action and never makes progress, even though nothing has crashed. |
| **LoRa / LoRaWAN** | LoRa is a long-range, low-power radio technology. LoRaWAN is the standard network system built on it, which relies on gateways; DR0 is its slowest data-rate setting. |
| **Mann–Whitney U / Wilcoxon signed-rank** | Tests of whether one group's values tend to be larger than another's. Mann–Whitney is for unrelated groups; Wilcoxon signed-rank (or sign test) is the paired version, used when both methods ran the same scenarios. |
| **Median / IQR** | The median is the middle value. The IQR (inter-quartile range) is the span covered by the middle half of the values. |
| **Mesh network** | A network where every device also relays messages for others, so no single device is essential. |
| **Meshtastic** | Popular open-source firmware (a device's built-in software) that turns off-the-shelf LoRa boards (such as T-Beam, Heltec or RAK) into a text-messaging mesh. |
| **Node** | One radio device in the mesh. |
| **ns-3 / ns3-gym** | ns-3 is a widely used network simulator; ns3-gym connects it to the standard interface used for reinforcement learning. |
| **Observation** | The 24 numbers PPO sees at each step, such as its position, battery level and the link quality to its neighbours. |
| **OLSR, B.A.T.M.A.N., Babel** | Well-known routing protocols (sets of rules for passing messages on) for mesh networks; they keep measuring link quality from regular hello messages. |
| **Oracle / global snapshot** | A full, up-to-date map of the whole network that the simulation hands to a planner. A real decentralised node wouldn't have it. |
| **Path loss / shadowing** | Path loss is how much a radio signal weakens over distance; the path-loss exponent controls how fast this happens. Shadowing (σ) adds random variation caused by obstacles. |
| **PDR (packet delivery ratio)** | The share of messages that get through. The paper uses the term for several different quantities (see P-22). |
| **Pearson r** | A number from −1 to +1 showing how closely two quantities move together. |
| **Post hoc subgroup** | A subset of the data chosen after looking at the results. Findings from it are weaker evidence. |
| **PPO (Proximal Policy Optimization)** | A standard training method for reinforcement learning, used here to train the route-choosing agent. |
| **p-value** | Roughly, how likely a difference this big would be if there were no real difference. Below 0.05 is the usual cut-off for "statistically significant". |
| **Radio horizon** | The distance beyond which the Earth's curvature blocks the straight line between two antennas; roughly 8–10 km for antennas 1–2 m above the ground. |
| **Rank-biserial correlation (r_rb)** | An effect size from −1 to +1 showing how strongly one group tends to beat the other. In the paper's Table II, negative values favour PPO. |
| **Reinforcement learning (RL)** | Training an agent by trial and error, rewarding good outcomes. |
| **Reward** | The score the agent receives during training. In ABOT: +100 for reaching a safe zone, −1 per step, and penalties for bad choices. |
| **RSSI** | Received signal strength, that is, how strong a signal is when it arrives. |
| **Safe zone** | The paper's word for the rescue point a route must reach; in the simulation, two fixed corner nodes. |
| **Seed** | A number that fixes all the random choices, so a scenario can be replayed exactly. A "training seed" is one independent training run. |
| **Sequence number** | A counter carried in each message, so a receiver can tell how many it missed. |
| **Spreading factor (SF12)** | A LoRa setting that trades speed for range. SF12 is the slowest and longest-range; even a short message takes more than a second to send. |
| **UWB (ultra-wideband)** | A short-range radio technology, very different from LoRa. |
| **Value estimate, V(s)** | PPO's prediction of how much future reward a situation is worth. ABOT's gossip shares these between nodes, and the paper calls them a "Q-table". |
