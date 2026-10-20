# ABOT Q&A prep plan: your chosen points, reviewed

**For:** presenting *ABOT: A Decentralized LoRa Mesh Communication Framework for Post-Disaster Environments* at IEEE R10-HTC 2026
**Date:** 2026-10-14
**Built from:** your list of points to prepare, [`ABOT-red-team-explained.md`](ABOT-red-team-explained.md) and [`ABOT-red-team-triage.md`](ABOT-red-team-triage.md), checked against the camera-ready paper. The same content is in the "Q&A prep review" sheet of [`ABOT-red-team.xlsx`](ABOT-red-team.xlsx).

## In short

- **You picked the right points.** All 10 points the triage marked "have an answer ready" are on your list.
- **The sets need work.** Some sets share only their ending ("…that's future work"), not their first sentence. Some points that need one answer are spread over different sets. P-01 is listed twice.
- **A few likely points are missing.** The biggest gaps are the abstract (P-08) and the simulator (P-32, P-17, P-24). P-38, P-14 and P-42 are also worth adding.
- **Some points get too much time.** P-16, P-43, P-21, P-31 and P-52 only come up if that detail is on a slide.
- **The fix: 9 sets instead of 17.** Learn the 9 opening lines by heart, then one follow-up line for each point.

## Your list

You picked 28 points and grouped them into 17 sets. Points in braces share one explanation; the rest stand alone.

- On their own: P-01, P-03, P-04, P-06, P-12, P-15, P-16, P-20, P-22, P-31, P-43, P-52.
- {P-02, P-41}
- {P-07, P-13}
- {P-10, P-11}
- {P-28, P-45, P-21, P-23}
- The "big set": {P-05, P-18, P-35, P-30, P-40, P-01, P-25}. P-01 is also on its own.

## How the sets were judged

Points belong in one set when their answers start with the same sentence. That first sentence is what you say when the question comes. Points that only share the last sentence, such as "…that's future work", are not one set.

## The 9 suggested sets

| Set | Name | Opening line to learn | Points | How well to know it | Note |
|---|---|---|---|---|---|
| A | What the main number is | "That number is a link-quality score for the nodes along the route, not the share of messages delivered. This paper doesn't measure SOS delivery to a rescuer." | P-01, P-04, P-07, P-22, P-08 (new), P-31 (backup) | By heart | Two ways in: "How many SOS messages reach a rescuer?" and "Isn't the planner chasing its own score?" Both end in the same place. If the "+5 per SOS delivered" reward comes up (P-31), it leads here too: in this version the agent's route doesn't carry the SOS message. |
| B | The task is easy | "Yes, it's easy. Each node has about 30 neighbours, so most routes are 2–3 hops and every method almost always reaches a safe zone. That's why we compare route length." | P-05, P-13, P-02, P-30, P-35, P-52 | By heart | Don't call the damage sweep "just a baseline": Section II of the paper claims it as a contribution. Say a harder version is needed (sparser meshes, and hops that can fail on weak links). |
| C | What's new | "We haven't compared ABOT with decentralised protocols or Meshtastic yet. Routing on link quality is a known idea; what we add is using it in a gateway-free LoRa mesh across five damage levels, with a simulator fast enough for RL." | P-10, P-11, P-25, P-24 (new) | By heart | Each part of "what we add" invites a follow-up: [5] already has hardware results (P-25), the damage levels barely change the results (set B), and the simulator (set D). |
| D | The fast simulator | "It's about 4.7× faster than our own reference simulator at the 10×10 grid we used, and up to 7.3× on a small grid. The two agree on which nodes are alive, not on traffic." | P-32 (new), P-17 (new) | One line | The 4.7× isn't printed in the paper. It comes from the saved benchmark results, so a listener holding the paper only knows 7.3×. |
| E | PPO and why RL | "The RL part is exploratory. PPO is in the same range as the classical planners, but not better than the fastest ones." | P-12, P-28, P-45, P-23, P-18, P-14 (new), P-42 (new), P-08 (new) | Opening by heart, the rest one line | The livelock: in one test scenario the agent kept picking a neighbour that had died. Hiding dead neighbours from its choices (action masking) is the standard fix. It's one scenario repeated at five damage levels, not a trend. Don't say "lower bound" or "the 8 slots hold PPO back". |
| F | Radio budget | "Beacon airtime is a real limit at this density, and the paper lists it. Dense areas would need slower beacons or faster radio settings." | P-06, P-20, P-16, P-43, P-21 | Opening by heart, the rest one line | Keep the numbers consistent: 4.4% per node assumes a beacon of about 20 bytes. With the paper's 34-byte header it would be about 6.0–6.6%. |
| G | How realistic the channel is | "The damage levels are relative stress settings. We checked them for internal consistency, not against real radio measurements." | P-15, P-41, P-27 (new, only if needed) | By heart | This set also answers "how realistic is the simulator?", one of the most likely questions. At the default damage level, a link delivers half its messages at about 2 km; at severe damage, at about 1 km. |
| H | Full view of the network | "In the simulation the planners get a full view of the network, as a best case. Sharing that view over the air, and the airtime it costs, isn't modelled yet." | P-03 | By heart | Keep this consistent with sets C and E: the planners have a full view as a best case, and PPO's inputs include a few whole-network hints. |
| I | Mistakes in the paper | "That's a mistake in the paper. Here's the right figure." | P-40, P-38 (new) | One line | P-40: the main comparison (0.267 vs 0.145) comes from 100 episodes; "250 per level" belongs to the damage sweep. P-38: "identical on all 100" is about a simulator check (the static planners take the same steps on both simulators), not about the two planners, which take 2.17 vs 3.23 steps. |

## Every point, one row

| ID | The problem in one line | Priority | Hard to defend | Your set | Suggested set | Change | Why | Prep level |
|---|---|---|---|---|---|---|---|---|
| P-01 | The paper never measures whether an SOS reaches a rescuer | Critical | 85 | Own + big set | A | Fix duplicate | It's on your list twice. Give it one home, with P-04, P-07 and P-22: they all come down to what the main number does and doesn't measure. | By heart |
| P-02 | Episodes last seconds, not a 33-minute window | Critical | 85 | {P-02, P-41} | B | Move | More than a wording fix. Episodes last tens of seconds, so failures, battery drain and the 25-minute link window barely act. The follow-up ("so what does your damage model test?") is set B's question. | One line |
| P-03 | The planner needs a full map the protocol never builds | Critical | 85 | Own | H | Keep | A question of its own: how does a node know the whole network? Keep the answer consistent with P-10 and P-12. | By heart |
| P-04 | The link scores can't be per-hop delivery chances | Critical | 82 | Own | A | Move | Same answer as P-07 and P-22: 0.267 and 0.145 are link-quality scores, not delivery chances. Answering them separately risks three different definitions of one number. | By heart |
| P-05 | Every method succeeds, so the test can't show robustness | Critical | 80 | Big set | B | Move | Its answer starts with "yes, the task is easy", not "future work". Don't call the damage sweep "just a baseline": the paper claims it as a contribution. | By heart |
| P-06 | Beacons alone would saturate the radio channel at this density | Critical | 80 | Own | F | Move | Same story as P-20: beacon airtime is high for each node, and the ~30 neighbours around each receiver add up. One answer for both keeps the numbers consistent. | By heart |
| P-07 | The winning planner is graded on the score it chases | Critical | 75 | {P-07, P-13} | A | Move | Same number as P-04 and P-22. Admit it: the planner picks routes using the same score it's measured on, so we only claim it changes which routes get picked. "It's a proof of concept" or "hardware will tell" doesn't fix this. | By heart |
| P-08 | The abstract's damage claims contradict the paper's own results | Major | 80 | Not on your list | A + E | Add | The abstract is the most-read part of the paper. It claims "improved packet delivery" (not measured) and "limitations of RL-based routing under extreme network collapse" (PPO's one failure happens at every damage level, even intact). A session chair may ask about it. | By heart |
| P-10 | None of the baselines is a decentralised protocol | Major | 78 | {P-10, P-11} | C | Keep | Good pair. Add P-25 and P-24: all four are "how does this compare, and what's new?" | By heart |
| P-11 | Live link-quality routing already exists in mesh protocols | Major | 75 | {P-10, P-11} | C | Keep | Good pair. Don't claim the metric is new; claim where you use it. | By heart |
| P-12 | PPO's 'local only' view includes whole-network information | Major | 75 | Own | E | Move | It's the trap inside "why RL?". Don't excuse PPO with "it only sees local information": the paper's own input list includes whole-network hints. Keep it consistent with the livelock answer: no "lower bound". | One line |
| P-13 | Claim that damage removes long-range shortcuts is not shown | Major | 75 | {P-07, P-13} | B | Move | Its answer is P-05's: every method almost always succeeds, so damage doesn't reach the routing task yet. If you paired it with P-07 because they share a fix, that fix also covers P-01, P-04 and P-05. | One line |
| P-14 | The paper doesn't say which trained model its results use | Major | 72 | Not on your list | E | Add | Section VI prints the scores of all three trained models (−0.67, 0.18, 0.71), so "which model did you test?" can be asked from the paper. The true answer is seed 0, the −0.67 one, so have a follow-up ready. A better use of time than P-31 or P-52. | One line |
| P-15 | The channel model's distances and damage presets look miscalibrated | Major | 72 | Own | G | Move | Pair it with P-41: both are range numbers from Fig. 2. It's also the "how realistic is the simulator?" question, which is very likely. | By heart |
| P-16 | The packet sizes don't add up | Major | 70 | Own | F | Move | Part of the radio budget. Only comes up if packet sizes are on a slide. Don't claim the real header is "compact": no specification exists. | Glance |
| P-17 | The simulator match on alive nodes is nearly guaranteed | Major | 70 | Not on your list | D | Add | If you call the fast simulator "validated", expect "validated on what?". The paper itself says the two simulators agree on which nodes are alive, not on traffic. | One line |
| P-18 | The gossip test was bound to find no difference | Major | 70 | Big set | E | Move | Its answer starts with "gossip made no difference; its merge step isn't connected", not "future work". Don't repeat the paper's line that the gossip arm "pays gossip's airtime": no gossip was sent during evaluation. | One line |
| P-20 | The airtime figure is miscalculated and cites the wrong rule | Major | 68 | Own | F | Move | Same answer as P-06. Don't say India has no duty-cycle limit, because that isn't verified. "ETSI is a European rule; airtime is the real limit either way" is enough. | One line |
| P-21 | The channel model assumes timing the design doesn't describe | Major | 68 | {P-28, P-45, P-21, P-23} | F | Move | It's about how nodes share the channel (slotted ALOHA needs a shared clock), not about PPO. Answer: it's a simplified collision model for the simulation, not a design for real radios. | Glance |
| P-22 | The paper uses PDR for three different quantities | Major | 65 | Own | A | Move | Same answer as P-04 and P-07. Label every PDR on your slides with what it measures. | By heart |
| P-23 | The livelock claim rests on one repeated scenario | Major | 65 | {P-28, P-45, P-21, P-23} | E | Keep | Good: part of the livelock set. It's one scenario repeated at five damage levels, reported for transparency. | One line |
| P-24 | Existing tools contradict the claimed research gap | Major | 65 | Not on your list | C | Add | Your "what's new" answer leans on a simulator fast enough for RL. The paper says LoRa simulators lack that, but tools such as ns3-gym exist (an outside fact: check it before quoting). Say ABOT offers a fast, mesh-specific environment, not the only one. | One line |
| P-25 | The closest prior work already has hardware results | Major | 62 | Big set | C | Move | The question is "[5] already has hardware, so what do you add?". "Hardware is next" doesn't answer it. Lead with what's new, then admit [5] has hardware results and ABOT doesn't yet. | By heart |
| P-27 | The channel model cites a source for a different radio | Major | 60 | Not on your list | G | Add | Only if a slide names where the path-loss numbers come from. The cited source [10] is a model for a different kind of radio (UWB). | Glance |
| P-28 | PPO's eight choices depend on how the nodes are numbered | Major | 60 | {P-28, P-45, P-21, P-23} | E | Keep | Good. Say the fixed list of 8 was a simplification and masking is the fix. Don't say the 8 slots hold PPO back: in the tested scenarios they always include a best next hop. | One line |
| P-30 | Clustered failures are motivated but never tested | Major | 55 | Big set | B | Move | Clustered failures were never tested. It will most likely come up inside "why RL?", because the paper's reason for RL is clustered failures (see P-42). | One line |
| P-31 | The +5 reward pays for traffic the agent doesn't control | Major | 55 | Own | A | Move | Only comes up if the reward table is on a slide. If it does, it leads to set A: in this version the agent's route doesn't carry the SOS message. | Glance |
| P-32 | The speed-up headline hides its grid size and mode | Major | 55 | Not on your list | D | Add | "Up to 7.3×" gives no grid size, so "at what size?" is a natural question. It's 4.7× at the 10×10 grid you used. | One line |
| P-35 | Nodes are assumed static, yet the paper mentions movement | Major | 50 | Big set | B | Move | One line is enough: the nodes are static in this study. Don't say nodes move. | Glance |
| P-38 | 'Identical on all 100' wrongly suggests the planners tie | Minor | 85 | Not on your list | I | Add | If you keep P-40, keep P-38: they're back-to-back sentences in the paragraph that holds your main result. P-38 is harder to defend (85 vs 75). | One line |
| P-40 | The 250-episode count is attached to the wrong comparison | Minor | 75 | Big set | I | Move | It's a mistake in the paper, not untested work. The 0.267 vs 0.145 result comes from the 100-episode main run; "250 per level" belongs to the damage sweep. Answering "future work" would sound wrong. | One line |
| P-41 | The multi-kilometre range holds only at milder damage levels | Minor | 60 | {P-02, P-41} | G | Move | Pairs with P-15: both are range numbers from Fig. 2. Say "about 2 km at the default damage level". | One line |
| P-42 | Replacing the planner is an aim, not a result | Minor | 55 | Not on your list | E | Add | Section I gives the reason for RL in one sentence: replace Dijkstra, and handle clustered failures better. Neither was shown. Expect it inside "why RL?". | One line |
| P-43 | The 51-byte size limit is borrowed from LoRaWAN | Minor | 50 | Own | F | Move | Part of the radio budget. Only comes up if the 51-byte limit is on a slide. Answer: it's a cautious size limit that also suits LoRaWAN radios. | Glance |
| P-45 | The livelock may be blamed on the wrong cause | Minor | 45 | {P-28, P-45, P-21, P-23} | E | Keep | Good. Blame "dead neighbours stay pickable", not "only 8 slots". Section VI of the paper already says dead neighbours stay addressable. | One line |
| P-52 | The reward–steps link is built in, not discovered | Minor | 25 | Own | B | Move | Only comes up if you show the reward–steps correlation. If you need to explain why you compare steps, say "reward is mostly set by the number of steps, so we compare steps directly". | Glance |

## What's wrong with the current sets

| # | Your choice | The problem | Why it matters | The fix |
|---|---|---|---|---|
| 1 | P-01 on its own, and P-01 in the big set | The same point is in two places. | You'd prepare two versions of your answer to the most likely question of the day. | Give it one home: set A. |
| 2 | The big set {P-05, P-18, P-35, P-30, P-40, P-01, P-25} | The points only share an ending ("…that's future work"). Their first sentences differ: P-40 is a mistake in the paper, P-25 needs "what's new" first, and P-18 is a no-difference result the paper already disclosed. | In Q&A the first sentence is what counts. A "future work" opening gives a wrong answer to P-40 and dodges the real question in P-25. | Split it across sets A, B, C, E and I. |
| 3 | P-04 on its own, P-07 with P-13, P-22 on its own | One answer is split across three places. | You risk giving three different definitions of one number, to questions a sharp listener will ask back to back. | Put all three in set A, with P-01. |
| 4 | {P-07, P-13} | P-13's answer is P-05's: every method almost always succeeds, so damage doesn't reach the routing task yet. If you paired them because they share a fix (send real messages along the routes, with hops that can fail), that fix also covers P-01, P-04 and P-05. | The grouping rule isn't applied the same way everywhere, so some answers end up in the wrong set. | P-07 to set A, P-13 to set B. |
| 5 | {P-02, P-41} | It works as two wording fixes, but P-02 is rated Critical (85): episodes are too short for failures, battery drain or the link window to matter. | Its follow-up ("so what does your damage model test?") is set B's question, which this pair doesn't prepare you for. | P-02 to set B. P-41 to set G, with P-15. |
| 6 | {P-28, P-45, P-21, P-23} | P-21 is about how nodes share the channel (slotted ALOHA), not about the livelock. | A mixed set makes you reach for the wrong answer. If the set meant "simplifications made for the simulator", then P-35, P-16 and P-43 would belong in it too. | P-21 to set F. Keep the other three together. |
| 7 | P-06, P-20, P-16 and P-43, each on its own | They're one story: airtime and packet sizes. | The numbers have to agree. 4.4% assumes a beacon of about 20 bytes; with the paper's 34-byte header it would be 6.0–6.6%. | Put all four in set F, with P-21. |
| 8 | P-12 on its own | It's the trap inside "why RL?". | The easy excuse, "PPO only sees local information", is exactly what P-12 disproves. It also has to match the livelock answer: no "lower bound", and no "the 8 slots hold PPO back". | Put it in set E. |

## Things not to say

| Point | Tempting line | Why not | Say instead |
|---|---|---|---|
| P-16 | "The real on-air header is compact." | No specification of the real header exists, so you can't back it up. | "The 34-byte layout is the simulator's internal record. The over-the-air format still needs to be specified." |
| P-20 | "India has no duty-cycle limit." | That hasn't been verified yet. | "ETSI is a European rule. Either way, airtime at this density is the real limit." |
| P-12, P-28, P-45 | "The 8 slots hold PPO back", or "PPO's result is a lower bound." | In the tested scenarios the 8 slots always include a best next hop, and the lower bound was never measured. | "The fixed list of 8 was a simplification. Hiding dead neighbours from the agent (masking) is the fix." |
| P-25 | "Hardware is next." (as the whole answer) | It doesn't say what ABOT adds over [5]. | "[5] has hardware results and we don't yet. What we add is …" |
| P-05 | "The damage sweep is just a baseline." | Section II of the paper claims the five-level sweep as a contribution. | "Every method almost always succeeds, at every damage level, so we compare route length. A harder version is needed." |
| P-07 | "It's a proof of concept; hardware will tell." | The problem is the choice of measure, and hardware doesn't change that. | "Partly, yes: the planner uses that same score. We only claim it changes which routes get picked." |
| P-18 | "The gossip arm paid the airtime cost." | No gossip was sent during evaluation. | "Gossip made no difference. Its merge step isn't connected yet." |
| Any | "That's future work," as a reflex. | Say "next" only for experiments you really plan. Several answers in a row that end in "future work" sound like the paper has no results. | "The experiment that would answer this is …" |

## Other advice

| # | Advice | Why |
|---|---|---|
| 1 | Say it first. Put one "limitations and next steps" slide in the talk that covers sets A, B and H. | When you volunteer an admission, it sounds honest, and it's what the reviewers asked for. When it's dragged out of you in Q&A, it sounds like a hole. |
| 2 | For the 7 Critical points (P-01 to P-07), prepare an admission that keeps the narrow claim, not a rebuttal. | They're rated 75–85 hard to defend. Arguing makes them worse. |
| 3 | Decide what goes on the slides first. | P-16, P-43, P-21, P-31 and P-52 only come up if that detail is on a slide. There's no slide deck in the prep folder yet. |
| 4 | Prepare the two standard questions as well: "Have you tested it on real hardware? How realistic is it?" (set G) and "Why use RL?" (set E). | They aren't red-team points, but they're the most likely questions of all. |
| 5 | Learn the 9 opening lines by heart, then one follow-up line for each point. | 9 sentences are easier to recall under pressure than 17 separate explanations. |

## Good choices to keep

- All 10 points the triage marked "have an answer ready" are on your list: P-01, P-03, P-04, P-05, P-06, P-07, P-10, P-11, P-22 and P-25.
- {P-10, P-11} is a real set: both are about how ABOT compares with existing mesh routing.
- {P-23, P-28, P-45} is the livelock, and those three belong together. Section VI of the paper already says dead neighbours stay addressable, so the honest cause is in print.
- Moving P-12, P-15 and P-20 up from "watch your wording" is sensible. They're the wording points a listener can most easily turn into a question.
