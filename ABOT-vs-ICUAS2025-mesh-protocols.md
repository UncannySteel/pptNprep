# ABOT compared with "OLSR, BATMAN-adv and Babel in UAV Mesh Networks" (ICUAS 2025)

*Written 2026-10-19. The other paper: B. A. Diniz, I. G. Ferrão, L. M. da Silva and K. Castelo Branco (University of São Paulo), "Comparative Performance Analysis of OLSR, BATMAN-adv, and Babel in UAV Mesh Networks", 2025 International Conference on Unmanned Aircraft Systems (ICUAS), Charlotte, NC, USA, pp. 496–503. DOI [10.1109/ICUAS65942.2025.11007820](https://ieeexplore.ieee.org/document/11007820).*

**What was actually read.** The full text is paywalled, and no free copy turned up. What IEEE Xplore shows publicly was read on 2026-10-19: the abstract, the captions of all four figures, all 12 references and the keywords. Anything below that goes beyond those is marked *(not in the abstract)* or *[ext]*. **[ext]** marks an outside fact taken from a protocol standard or general knowledge, not from either paper. Each [ext] fact names its source; check it before quoting it on stage. ABOT facts come from the camera-ready paper, with code paths given relative to `<CODE>/darwinV2/`.

---

## Bottom line

1. **It isn't a competitor.** The two papers answer different questions.
   - The São Paulo paper takes three *existing* Wi-Fi mesh routing protocols and tests which works best for drone swarms, on real Raspberry Pi devices.
   - ABOT *proposes* a new LoRa mesh design for disaster zones, plus a fast simulator for training routing agents, and tests it only in simulation.
2. **The overlap is real, and it matters for Q&A.** Like ABOT, all three protocols are decentralised, every node relays, and nodes measure link quality from regular "hello" messages. OLSR with its usual link-quality add-on is close in spirit to ABOT's `dijkstra_dynamic` planner: shortest path over a map, where each link costs about 1 ÷ its delivery rate. The ABOT paper never cites or compares against any of the three (§4).
3. **Their paper is ahead on evidence.** They used real hardware, measured packet loss and delay, measured CPU and memory use, varied the traffic load, and tested mobility. ABOT has none of these. Its own limitations section says so for hardware (VI), and the red team said so for delivery and delay (P-01).
4. **ABOT is ahead on scope.** It models LoRa's radio limits, five levels of damage and node failures on a 100-node mesh, its simulator scales to 900 nodes, and it offers an RL training interface. Their abstract mentions none of these.
5. **The best use of this paper for your talk is one answer:** "Why not just use OLSR, BATMAN or Babel?" With their default settings, these protocols would need more airtime than a LoRa channel has (§6). Concede the other half honestly: they measured on hardware, and ABOT hasn't yet.

---

## 1. The other paper in plain English

**What they did**
- They ran three standard mesh routing protocols, OLSR, BATMAN-adv and Babel, on Raspberry Pi devices "in a real environment" (abstract).
- They compared four things "under different loads", one figure each (captions of Figs. 1–4):
  1. packet loss;
  2. delay;
  3. CPU usage;
  4. RAM usage.
- They also looked at "highly-mobility scenarios" (abstract).

**What they found** (the abstract, paraphrased)
- **OLSR** was the most stable and efficient as the traffic load varied, which they put down to its quick route adaptation.
- **Babel** had the lowest delay when nodes moved a lot, which they put down to its fast route updates.
- **BATMAN-adv** worked well in some conditions, but used more resources and became unstable under heavy traffic.

**What they claim as the contribution:** a detailed comparison of the three in a real environment, to help pick the right protocol for each application.

**What couldn't be seen without the full text**
1. **How many devices they used.**
2. **The radio.** The abstract doesn't name it. These protocols normally run over Wi-Fi, and Raspberry Pis have Wi-Fi built in, so it's almost certainly Wi-Fi.
3. **Whether the Pis were flying.** They might have been mounted on drones, or on the ground with movement emulated.
4. **What "different loads" means**, and the actual numbers.
5. **Whether they used any statistical tests.**
6. **Whether they measured temperature.** The keywords include "Thermal stability" and "Thermal Efficiency", but no figure caption mentions temperature.

If you can get the PDF (for example through Amity's library), these gaps can be filled in.

**Their reference [2]**, Guillén-Pérez et al. (*Applied Sciences*, 2021), is another real-world drone test of routing protocols. If someone in the audience knows this area, they may know that one too.

---

## 2. The three protocols in plain English

You don't need the details. You need just enough to recognise the names if someone raises them, and to see where each overlaps with ABOT.

| Protocol | How it works, in one breath | Its default "hello" timing [ext] | Closest part of ABOT |
|---|---|---|---|
| **OLSR** (Optimized Link State Routing) | Every node says hello to its neighbours and lists who it can hear. Selected relay nodes then flood link information across the whole network, so **every node builds a map** of the network and computes shortest paths over it. The widely used olsrd implementation adds a link-quality cost (ETX, below). | HELLO every 2 s, network-wide topology message every 5 s (RFC 3626 §18.2) | `dijkstra_dynamic`: shortest path over a full map, with link quality as the cost |
| **BATMAN-adv** ("Better Approach To Mobile Adhoc Networking", advanced) | Every node regularly broadcasts a small "I exist" message, and the others pass it on. In the classic version, each node counts how many of those messages arrive through each neighbour, and sends traffic through the neighbour that delivers the most. **No node holds a map**; each knows only its best next hop. It runs inside the Linux kernel, at the network-card level (layer 2). | Originator message every 1 s (Linux kernel docs, `orig_interval` 1000 ms) | ABOT's link monitoring as the paper describes it: counting what arrives over a sliding window of recent packets (III) |
| **Babel** | Neighbours tell each other how costly their routes are, and each node keeps the cheapest one. On wireless links the cost comes from how many hellos get lost. A rule built into the protocol prevents routing loops. It runs over ordinary internet packets (UDP port 6696). | Hello every 4 s (RFC 8966 App. B) | ABOT's live link-quality score, used as a route cost |

**ETX ("expected transmission count")** is the standard link-quality cost these protocols use [ext: De Couto et al., MobiCom 2003]. A link's cost is 1 ÷ (share of packets that get through in one direction × share that get through in the other). A link that loses half its packets one way and none the other costs 2; if it loses half both ways, it costs 4.
- **ABOT's planner uses the same shape.** Its edge cost is 1 ÷ max(score, 0.01), where the score is the average of the two end nodes' link scores (`src/train/baselines.py:339-342`).
- **Why it matters:** a networking listener may recognise ABOT's "routing on live link state" as a known idea. That's fine, provided you don't present it as new (§7).

---

## 3. Side by side

| | **ABOT** (R10-HTC 2026) | **The São Paulo paper** (ICUAS 2025) |
|---|---|---|
| **Question asked** | Can a gateway-free LoRa mesh route distress messages by live link quality after a disaster, and can RL learn the routing? | Which existing mesh protocol suits drone swarms best? |
| **Kind of contribution** | A new design, a fast simulator, and an exploratory RL agent | A benchmark of three existing protocols |
| **Setting** | Post-disaster ground mesh: survivor devices and relays | Drone swarms; "dynamic ad-hoc infrastructures without fixed support" (abstract) |
| **Radio** | LoRa at 865 MHz, SF12, 125 kHz (Table I) | Not stated in the abstract; almost certainly Wi-Fi |
| **Raw data rate** | About 293 bit/s (computed from Table I's SF and bandwidth plus the code's 4/5 coding rate, `src/comm/phy.py:20`; `tools/lora_airtime.py`) | Wi-Fi: typically millions of bit/s or more [ext] |
| **Largest packet** | 51 B (Table I), which takes 2.47 s to send (IV) | Wi-Fi frames carry about 1,500 B [ext] |
| **Range per hop** | 1,500 m assumed (III) | Wi-Fi: typically tens to a few hundred metres [ext] |
| **Number of nodes** | 100 (10×10 grid); up to 900 for speed tests (V) | Not in the abstract; a Pi testbed is usually a handful |
| **Nodes move?** | No. Positions are fixed on a grid; the code has no mobility model | Yes: "highly-mobility scenarios" (abstract) |
| **Damage and failures** | Five radio-damage levels, plus random node failures (III) | Not in the abstract |
| **Traffic load varied?** | No. Fixed schedule: an SOS every 10 steps, gossip every 5, beacons every 3 (III) | Yes: "different loads" (all four figures) |
| **How routes are chosen** | Shortest path on a full network map, either by hop count or weighted by link score. The planners are handed the map by the simulator (III). PPO picks among 8 neighbours. | By each protocol's own mechanism (§2) |
| **How the map or routes are learned** | Beacons carry only the sender's ID (III). A ROUTE_UPDATE message type is defined (`src/comm/packet.py:40`), but the simulator never sends one; only a unit test builds one (`tests/test_sim.py:208`) | Each protocol spreads its own routing information |
| **Evidence** | Simulation only (VI) | Real devices (abstract) |
| **Metrics** | Steps to a safe zone; a node-level link-quality score; success; reward; simulator speed | Packet loss, delay, CPU, RAM |
| **End-to-end delivery or delay** | Not measured (red team P-01) | Measured: packet loss (Fig. 1) and delay (Fig. 2) |
| **Device resources** | Not measured | CPU (Fig. 3) and RAM (Fig. 4) |
| **Statistics** | Rank-based pairwise tests with corrected p-values and effect sizes (Table II) | Not visible in the abstract |
| **Honest scope** | "Exploratory" RL; "entirely in simulation" (I) | A practical guide to choosing a protocol (abstract) |

---

## 4. What the two share

1. **No central controller; every node relays.**
   - ABOT: "every node simultaneously functions as a terminal and a relay" (III). The three protocols work the same way.
   - Why it matters: being gateway-free sets ABOT apart from LoRaWAN, not from mesh networking in general. Say "unlike LoRaWAN", as the abstract does, not "unlike existing networks".
2. **Regular hello messages to sense neighbours and link quality.**
   - ABOT: beacons every 30 s; each receiver works out link quality from what it hears (III).
   - OLSR, BATMAN-adv and Babel all do this, every 1–4 s by default [ext].
   - Why it matters: ABOT's link-state monitoring layer is a LoRa-paced version of something mesh protocols already do. The new part is doing it on LoRa's tiny airtime budget, and that is exactly the part ABOT's results haven't tested (§5, D7).
3. **Routes chosen by link quality, not just hop count.**
   - ABOT's `dijkstra_dynamic` uses a cost of 1 ÷ link score per hop, ETX-shaped (§2). OLSR with ETX and Babel do the same kind of thing [ext].
   - Why it matters: Gap 2 in ABOT's Section II says link-quality routing elsewhere "acts on static topology or on failure triggered recomputation". That holds for the disaster-LoRa papers ABOT cites ([7], [8]). It doesn't hold for these three protocols, which update link costs all the time. This is the same caution the lit-gap review gives (`ABOT-lit-gap-review.md` §1, rule 1).
4. **Reacting to change without waiting for a failure alarm.**
   - ABOT replans when a node ahead dies *or* its score drops below 0.5 (`baselines.py:312-320`). The three protocols keep refreshing routes continuously.
   - Why it matters: ABOT's "before it fails outright" (III) is a fair contrast with failure-triggered schemes, but not with these protocols.

---

## 5. Where they differ, and why each difference matters

**D1. A new design, versus choosing between existing ones**
- What: ABOT builds something new; they test existing tools.
- Why it matters: they don't need to prove a new idea works, just measure the options carefully. ABOT has to show both that its design works and that it beats something. That is a harder burden, and it's why ABOT's choice of baselines gets questioned (P-10).

**D2. LoRa versus Wi-Fi**
- What: LoRa at SF12 sends about 293 bit/s, with a 51-byte limit and 2.47 s per full packet. Wi-Fi sends millions of bit/s [ext]. LoRa reaches kilometres; Wi-Fi reaches tens to hundreds of metres [ext].
- Why it matters:
  1. Their findings don't carry over to LoRa. "BATMAN-adv is unstable under heavy traffic" is a Wi-Fi result.
  2. The bottleneck is different. On Wi-Fi it's CPU, memory and congestion at high speed. On LoRa it's airtime: how many seconds per hour each node may transmit. §6 works this through.

**D3. Real devices versus simulation**
- What: their numbers come from real devices; every ABOT number is a simulation estimate (VI).
- Why it matters:
  1. Real measurements include everything a simulator can leave out: real interference, hardware quirks, software overhead.
  2. ABOT's own two simulators disagree on delivery under contention (KS p < 10⁻³; IV). Without hardware, ABOT can't say which is closer to reality.
  3. The trade-off runs the other way on scale. A Pi testbed is usually small. ABOT ran a 100-node mesh at five damage levels, and scaled its simulator to 900 nodes; no small testbed could do either.

**D4. Packet loss and delay, versus route length and a link score**
- What: they report packet loss and delay. ABOT reports steps to a safe zone and a node-level link-quality score, and never counts SOS messages reaching a rescuer or times them (red team P-01; context §11, §16).
- Why it matters:
  1. Packet loss and delay are what a networking audience expects. Their paper shows that even a small hardware study reports them.
  2. ABOT's abstract says "improved packet delivery performance", but nothing in ABOT measures delivery (P-08). Set against a paper that does measure it, the gap is easier to see.

**D5. Varying the traffic load**
- What: they test several loads. ABOT uses one fixed traffic schedule (III).
- Why it matters: ABOT's own reference [1] (its Introduction) says node density and traffic load together are what limit LoRa network availability. ABOT models collisions (slotted ALOHA with 6 dB capture), but never turns the load up to see when the mesh breaks.

**D6. Mobility versus damage**
- What: they test moving nodes. ABOT's nodes never move: the code has no mobility model, even though Section III says the mesh reconfigures "as nodes fail or move out of range". ABOT instead tests radio damage and node failures.
- Why it matters:
  1. Each paper tests a stress the other doesn't.
  2. For ABOT, "move out of range" is described but never simulated. Don't claim mobility handling.
  3. ABOT's failure model is also mild in practice: a node on the route dies in only about 1–3% of trips (context §15).

**D7. Who builds the map**
- What: OLSR spends regular network-wide messages so that every node gets a map; Babel and BATMAN-adv spread route information hop by hop [ext]. ABOT's planners are handed the full map by the simulator (III), and beacons carry only the sender's ID (III). The ROUTE_UPDATE type is defined (`src/comm/packet.py:40`), but the simulator never sends one.
- Why it matters:
  1. Building and refreshing that map is the expensive part of mesh routing. ABOT's results don't pay that cost.
  2. A listener who knows OLSR might put it as: "your Dijkstra planner is OLSR with the map given for free". That's essentially fair (red team P-03; context §19).
  3. On LoRa, distributing a map is far costlier than on Wi-Fi (§6). That's the real open problem, and a good thing to name as future work.

**D8. Device resources**
- What: they measured CPU and RAM on Raspberry Pis. ABOT is meant to run as firmware on much smaller LoRa boards (T-Beam, Heltec, RAK; VI Future Work), but measured nothing on any device.
- Why it matters: those boards have far less memory and processing power than a Raspberry Pi [ext]. Their finding that one protocol (BATMAN-adv) used more resources shows that resource use can separate protocols even on a Pi. For ABOT it's untested, which is one more reason the hardware step matters.

**D9. Scale and repeatability**
- What: ABOT runs thousands of seeded episodes (100 per agent per grid; 250 per agent per damage level) with significance tests. Their abstract mentions no repeat count or statistics; that may just be the abstract.
- Why it matters: this is a genuine ABOT strength, and it comes from using a simulator. It is the fair counterweight to D3.

---

## 6. "Why not just run OLSR, BATMAN-adv or Babel over LoRa?"

This is the most likely question this paper could prompt. The answer is arithmetic about airtime.

**One LoRa packet at ABOT's settings takes 1.32 s (20 B) to 2.47 s (51 B) to send** (the Semtech formula with ABOT's constants, `src/comm/phy.py:54-88`; the paper quotes the 2.47 s in IV; run `python -I tools/lora_airtime.py`).

| Protocol at its default timing | What it would mean at SF12 | Why it doesn't fit |
|---|---|---|
| **BATMAN-adv**, a message every 1 s [ext] | Even a 20-byte message takes 1.32 s to send | Each node would need about 130% of the channel's time for its own hellos, before relaying anyone else's |
| **OLSR**, a HELLO every 2 s, listing every neighbour [ext] | Each IPv4 neighbour address takes 4 bytes (RFC 3626 §6.1). At ABOT's average of 30.7 neighbours, that's about 120 bytes of addresses | More than twice the 51-byte limit, before any headers. On top of that, a network-wide topology message goes out every 5 s |
| **Babel**, a hello every 4 s, sent as internet (UDP over IPv6) packets [ext] | The IPv6 and UDP headers alone take 48 of the 51 bytes | Almost no room for the message itself. Even at 51 bytes every 4 s, that's about 62% of the channel's time for one node's hellos |
| **ABOT**, a beacon every 30 s carrying only the sender's ID | 1.32 s every 30 s | Still about 4.4% of airtime, which the paper itself lists as a limitation (VI) |

**Caveats, so you aren't caught out**
1. **The timers can be changed.** All three protocols let you slow their hellos down. A slowed-down version would use less airtime, but would react to changes far more slowly. Nobody tested that in ABOT, so don't claim it fails.
2. **Header compression exists** (6LoWPAN-style) [ext]. It shrinks IP headers on low-power radios, so the Babel row is about the default setup, not every possible one.
3. **ABOT didn't compare against any of them.** So "ABOT beats OLSR on LoRa" is not a claim you can make. The safe claim: "they were designed for Wi-Fi's bandwidth; ABOT's design starts from LoRa's airtime budget."

---

## 7. For the talk

### Likely questions, with short answers

**Q1. "Why not use an existing mesh protocol like OLSR, BATMAN or Babel?"**
> "They were built for Wi-Fi, which carries thousands of times more data than LoRa at our settings. At their default timings, their hello messages alone would need more airtime than a LoRa channel has. One LoRa packet takes over a second to send. So ABOT starts from LoRa's airtime budget: 30-second beacons carrying just an ID. We haven't compared against slowed-down versions of those protocols; that's a fair next baseline."

**Q2. "A team at ICUAS 2025 compared mesh protocols on real hardware. You only simulated."**
> "Yes, and that's the right next step for us. Their study measured packet loss, delay, CPU and memory on a real testbed. Ours ran a 100-node simulated LoRa mesh at five damage levels, which a small testbed can't do. The simulation tells us what to test; hardware has to confirm it."

**Q3. "Isn't routing on live link quality just OLSR with ETX?"**
> "The idea is related, and we don't claim the metric is new. What we looked at is that idea on LoRa, in a mesh with no gateway, across damage levels. In our simulation, putting the live score into route choice is what changes the routes; a planner that ignores it picks routes with about half the score."
- Keep to "changes which routes get picked". Don't say "better delivery" (P-07, P-22).

**Q4. "They measured packet loss and delay. What's your delivery rate?"**
> "We don't report one yet. Our results measure which routes get picked and their link quality, not how many distress messages reach a rescuer or how fast. That's the next experiment."
- This is the P-01 answer. Their paper makes the gap more visible; it doesn't change the answer.

**Q5. "Did you test mobility or traffic load?"**
> "No. Our nodes are fixed, and the traffic schedule is fixed. We stressed the radio instead, across five damage levels. Load and mobility are both open."

### Say / don't say

| Don't say | Say instead | Why |
|---|---|---|
| "No mesh protocol routes on live link quality" | "In the disaster-LoRa work we reviewed, routing doesn't use live link quality" | OLSR-ETX, BATMAN-adv and Babel all do [ext] |
| "ABOT outperforms OLSR / BATMAN / Babel" | "We haven't compared against them; they were designed for Wi-Fi bandwidth" | No such comparison exists |
| "OLSR / Babel can't run on LoRa" | "At their default timings they'd need more airtime than LoRa has" | Timers can be slowed (§6, caveat 1) |
| "Studies show BATMAN is unstable" (as a point about LoRa) | Leave it out, or say "on Wi-Fi" | Their results are Wi-Fi results (D2) |
| "ABOT handles mobility" | "ABOT reconfigures around failed nodes; mobility is untested" | No mobility model in the code (D6) |
| "Like their study, we measured delivery" | "We measured route choice and link quality" | ABOT has no delivery measure (D4) |

### Should you mention this paper on stage?
- **Not on a slide.** It isn't in the camera-ready reference list, and it's about drones and Wi-Fi.
- **Keep it for Q&A.** It's a concrete, recent example for Q1 and Q2. You don't need to have read the full text: the abstract and the airtime arithmetic are enough to answer those.

---

## 8. Sources

**The other paper** (IEEE Xplore, read 2026-10-19): abstract, figure captions, reference list and keywords from https://ieeexplore.ieee.org/document/11007820. The full text was not available.

**Outside facts [ext]**
- OLSR: RFC 3626. §6.1 gives the HELLO format (each neighbour address is a 32-bit row, i.e. 4 B for IPv4); §18.2 gives HELLO_INTERVAL = 2 s and TC_INTERVAL = 5 s.
- Babel: RFC 8966. UDP port 6696 and IPv6 multicast ff02::1:6; App. A.2.2 covers link cost on wireless links; App. B suggests a 4 s multicast Hello interval.
- BATMAN-adv: Linux kernel documentation (networking/batman-adv). It operates at layer 2 only, and the docs show `orig_interval` as 1000 ms.
- ETX: De Couto, Aguayo, Bicket and Morris, MobiCom 2003.
- Wi-Fi data rate, frame size and range; header compression; the memory of LoRa boards: general knowledge. Check before quoting.

**ABOT**
- The camera-ready paper: Sections I–VI and Table I.
- Code: `src/train/baselines.py:312-320, 339-342`; `src/comm/packet.py:40` and `tests/test_sim.py:208` (the only uses of ROUTE_UPDATE); `src/comm/phy.py:14-22, 54-88`. A search of every `.py` file in `darwinV2/` finds no mobility model.
- `context.md` §11, §15, §16 and §19; `ABOT-lit-gap-review.md`.
- Airtime figures: `tools/lora_airtime.py` (a re-implementation of ABOT's formula; nothing in `<CODE>` was run).
