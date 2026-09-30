# 🛢️ eRTMAC-NWIS — Complete User Guide
### How to Use Every Part of the Platform (Step by Step)

> [!TIP]
> **Live Site:** [https://ertmac-nwis-q4yt.onrender.com/](https://ertmac-nwis-q4yt.onrender.com/)
> Open this link and follow along!

---

## 📍 Step 0: Open the Website

1. **Go to** [https://ertmac-nwis-q4yt.onrender.com/](https://ertmac-nwis-q4yt.onrender.com/)
2. **Wait 10-30 seconds** — the free Render server "wakes up" after being idle (this is normal, it's a free plan)
3. You'll see the **Landing Page** — a dark-themed page with an oil rig illustration and the text: *"Every Well Has a History. Make It Part of Your Next Decision."*

---

## 🏠 Page 1: The Landing Page (Home)

**URL:** `/` or `/index.html`

### What You See:
- **Top Navigation Bar** — a horizontal bar with links to every module
- **Hero Section** — big headline, a description of the project, and two buttons
- **Module Cards** — scroll down to see cards for each feature
- **Visual Artifacts** — images of underground models and control rooms
- **Statistics** — numbers like "5 Real Wells", "10 Documented Incidents"

### What to Do Here:

| What You Want | What to Click |
|---|---|
| **See all the features at a glance** | Scroll down to the **"Dedicated Engineering Workspaces"** section |
| **Go to the main dashboard** | Click **"⚡ Command Center"** in the top nav bar, OR click the big gold button **"Launch Command Center →"** on the first card |
| **Watch live rig sensors** | Click **"📡 Live Rig Monitor"** in the top nav |
| **Search old drilling reports** | Click **"🛡️ Verified AI Search"** in the top nav |
| **Replay past drilling operations** | Click **"⏱️ Time Machine"** in the top nav |
| **See underground rock layers** | Click **"💎 Rock Matcher"** in the top nav |
| **Find nearby wells on a map** | Click **"🛰️ Nearby Wells"** in the top nav, OR click the blue button **"Launch Offset Radar →"** |

### The Module Cards (Scroll Down):

When you scroll down the landing page, you'll see **10 module cards**. Here's what each one does:

| Card # | Card Name | What It Does | Button to Click |
|---|---|---|---|
| ⭐ Main | **NWIS NEXUS — Unified Command Center** | The "everything in one place" dashboard | "Launch Command Center →" |
| 📡 | **NWIS PULSE — Live Rig Monitor** | Shows live sensor data from the drilling rig | "Open Live Rig Monitor →" |
| 🛡️ | **NWIS Sentinel — Verified AI Search** | Ask questions, get answers from real past reports | "Open Verified AI Search →" |
| ⏱️ | **NWIS Chronos — Drilling Time Machine** | Replay past operations to test the system | "Open Drilling Time Machine →" |
| 💎 | **NWIS GeoCore — Rock Layer Matcher** | Match rock layers between wells | "Open Rock Layer Matcher →" |
| 🛰️ | **Nearby Wells Radar** | Find wells near a location on a map | "Open Nearby Wells Radar →" |
| 🌋 | **3D Rock Layers** | View underground rock layers in 3D | "Open 3D Rock Layers →" |
| ⚡ | **Ahead-of-Bit Hazard Radar** | See dangers coming 50-150m ahead of the drill | "Open Hazard Radar →" |
| 📄 | **Document & Report Reader** | Upload and read PDF drilling reports | "Open Report Reader →" |
| 🤖 | **Drilling AI Chat Assistant** | Chat with the AI in plain English | "Open AI Chat Assistant →" |
| 📊 | **Blind Well Test** | Test the system's accuracy on past data | "Open Blind Well Test →" |

> [!IMPORTANT]
> **Recommended starting order:**
> 1. Start with **Command Center** (nexus.html) — see the overview
> 2. Then try **Verified AI Search** (sentinel.html) — ask a question
> 3. Then explore **Live Rig Monitor** (pulse.html) — watch sensors
> 4. Then try **Time Machine** (chronos.html) — replay history

---

## ⚡ Page 2: Command Center (nexus.html) — THE MAIN DASHBOARD

**URL:** `/nexus.html`  
**How to get here:** Click "⚡ Command Center" from any page's nav bar

### What You See:

This is the **"everything at once"** dashboard. It has multiple panels:

#### Top Banner
- **System Status Pill** — shows "OPERATIONAL" (green), "DEGRADED" (yellow), or "STANDBY" (grey)
- **Title:** "NWIS NEXUS — Unified Operations Command Center"

#### Main Panels (what each section shows):

| Panel | What It Shows | What You Can Do |
|---|---|---|
| **System Health** | Status of each module (GeoCore, Pulse, Sentinel, Chronos) — green = working, red = down | Just watch — it updates automatically |
| **Danger Score (CPI)** | A number from 0-100 showing how urgent the current situation is | Green (0-30) = safe, Yellow (31-60) = watch out, Red (61-100) = danger |
| **Active Warnings** | List of current safety alerts | Click on any alert to see details |
| **Recent Events** | Timeline of what happened recently | Scroll through to see shift activity |
| **Operations Log** | Tamper-proof log of all actions taken | Every entry is digitally signed |
| **Well Comparison** | Side-by-side comparison of wells | Select wells from dropdowns |

### What to Do Here:

1. **Just look at the dashboard** — it gives you a high-level overview
2. **Check the Danger Score** — if it's low (green), things are normal
3. **Read the Active Warnings** — these are the most important alerts right now
4. **Scroll the Operations Log** — this shows what happened during the shift

> [!TIP]
> **Think of this page like the cockpit of an airplane.** You see all the instruments at once. If something turns red, pay attention to it.

---

## 🛡️ Page 3: Verified AI Search (sentinel.html) — ASK QUESTIONS, GET PROVEN ANSWERS

**URL:** `/sentinel.html`  
**How to get here:** Click "🛡️ Verified AI Search" from any page's nav bar

### What You See:

A **three-column layout:**
- **Left Panel** — Search filters and settings
- **Middle Panel** — Your question box and AI answers
- **Right Panel** — Evidence and proof documents

### How to Use It (Step by Step):

#### Step 1: Type a Question
In the middle panel, you'll see a **text box** (search bar). Type your question in plain English:

**Example questions you can try:**
- *"Were there any stuck pipe events in the Hugin formation?"*
- *"What mud weight was used in well F-14?"*
- *"Any lost circulation incidents near 2800 meters?"*
- *"What happened when drilling through the Skade formation?"*

#### Step 2: (Optional) Set Filters in the Left Panel
Before searching, you can narrow down results:

| Filter | What It Does | Example |
|---|---|---|
| **Rock Layer Filter** | Only search within a specific underground formation | Select "Hugin Sandstone" |
| **Distance Filter** | Only search wells within a certain distance | Set to "5 km" |
| **Hazard Type Filter** | Only search for a specific type of danger | Select "Stuck Pipe" |

#### Step 3: Click "Search" or press Enter
The AI will search through all old drilling reports and give you an answer.

#### Step 4: Read the Answer
The answer will appear in the middle panel. It will include:
- **The answer itself** — in plain English
- **Confidence score** — how sure the system is (e.g., 87%)
- **Source well name** — which well this info came from

#### Step 5: Check the Evidence (Right Panel)
The right panel shows the **Evidence Passport** — the proof for the answer:
- **Which report** the info came from (e.g., "DDR Report #44")
- **Which page** in the report
- **The exact text** that was found
- **A digital fingerprint** (SHA-256 hash) proving the document wasn't changed

> [!IMPORTANT]
> **If the system can't find strong evidence, it will say: "No historical evidence documented."** This means it's being honest — it won't guess or make things up.

---

## 📡 Page 4: Live Rig Monitor (pulse.html) — REAL-TIME SENSOR DASHBOARD

**URL:** `/pulse.html`  
**How to get here:** Click "📡 Live Rig Monitor" from any page's nav bar

### What You See:

Live gauges and charts showing sensor data from the drilling rig, like the dashboard of a car.

### The Main Panels:

| Panel | What It Shows | What the Numbers Mean |
|---|---|---|
| **Standpipe Pressure (SPP)** | Pressure of mud being pumped down the drill pipe | Normal: steady. Sudden spike = blockage or kick |
| **Torque** | How hard the drill is twisting | Rising = drill might be getting stuck |
| **Rate of Penetration (ROP)** | How fast the drill is going forward (meters/hour) | Dropping = drill is struggling |
| **Flow In vs Flow Out** | Mud going down vs mud coming up | If more comes up than goes in = underground fluid entering (KICK!) |
| **Pit Volume** | Total amount of mud in the surface tanks | If it rises unexpectedly = gas or water pushing mud out |
| **Sensor Health** | Whether the sensors are sending good data | 🟢 Healthy / 🟡 Degraded / 🔴 Offline |

### What to Do Here:

1. **Watch the gauges** — they update in real-time (every second when connected to a rig)
2. **Look for warning colors:**
   - 🟢 **Green** = everything normal
   - 🟡 **Yellow** = something unusual, keep watching
   - 🔴 **Red** = danger! Check immediately
3. **Read the Alert Cards** — if a danger pattern is detected (stuck pipe, kick, packoff), an alert card appears at the top

### Understanding the Alerts:

| Alert Type | What It Means | What to Do |
|---|---|---|
| **⚠️ Stuck Pipe Warning** | Torque rising + ROP dropping | Consider pulling up the drill to free it |
| **⚠️ Blockage Warning** | Pressure spiking + erratic torque | Check if cuttings are blocking the well |
| **🚨 Kick Alert** | Pit volume rising + flow imbalance | Follow well control procedures immediately |

> [!TIP]
> **In demo mode**, the system simulates sensor data so you can see how it works even without a real rig connected. The data you see is from the real Equinor Volve oil field — just replayed.

---

## ⏱️ Page 5: Drilling Time Machine (chronos.html) — REPLAY PAST DRILLING

**URL:** `/chronos.html`  
**How to get here:** Click "⏱️ Time Machine" from any page's nav bar

### What You See:

A **time-travel simulator** that replays past drilling operations day by day.

### How to Use It (Step by Step):

#### Step 1: Select a Well to Replay
You'll see a **dropdown menu** with well names. Pick one:

| Well Name | What Happened to It |
|---|---|
| **NO-15/9-F-12** | Target well — had specific formation challenges |
| **NO-15/9-F-14** | Experienced lost circulation (mud loss) at Skade formation |
| **NO-15/9-F-15** | Had stuck pipe events |

#### Step 2: Click "Run Replay" or "Start Simulation"
The system will start replaying that well's drilling operation from the beginning.

#### Step 3: Watch the Timeline
As the replay runs, you'll see:
- **Current date** — what date is being simulated
- **Current depth** — how deep the drill has reached
- **Active warnings** — what the system would have warned about at that point in time
- **What actually happened** — the real event that occurred

#### Step 4: Check the Temporal Firewall
Notice the badge that says **"Temporal Firewall Active"** — this means:
- The system can only see data from BEFORE the current replay date
- It can NOT cheat by looking at future data
- This proves the warnings are genuine predictions, not hindsight

#### Step 5: See the Results
At the end of the replay, you'll see:
- **How many warnings were correct** (accuracy)
- **How far in advance** warnings were given (in meters)
- **Any false alarms** that were triggered

> [!TIP]
> **Example scenario:** Select well F-14, run the replay. When the drill reaches ~2,700m depth, you should see a warning about "Lost Circulation risk" at the Skade formation — and this actually happened in real life! The system predicted it using data from OTHER nearby wells.

---

## 💎 Page 6: Rock Layer Matcher (geocore.html) — UNDERGROUND MAP

**URL:** `/geocore.html`  
**How to get here:** Click "💎 Rock Matcher" from any page's nav bar

### What You See:

A geological intelligence page showing 3D well paths, rock layer comparisons, and well similarity rankings.

### The Main Panels:

| Panel | What It Shows |
|---|---|
| **Well Trajectory View** | 3D visualization of well paths going underground — you can see how they curve |
| **Formation Tops Table** | A table showing at what depth each rock layer starts for each well |
| **Well Similarity Rankings** | A list of nearby wells ranked by how similar their geology is (highest match % first) |
| **Depth Comparison Chart** | Side-by-side chart comparing depths across wells |

### How to Use It:

#### Step 1: Select a Target Well
Choose the well you're currently drilling (or interested in) from the dropdown.

#### Step 2: See the Ranked List
The system shows you nearby wells sorted by **geological similarity** (not just distance!). Each has a match percentage:
- **94% match** = very similar geology, warnings from this well are highly relevant
- **60% match** = somewhat similar, be cautious with comparisons
- **30% match** = very different, warnings may not apply

#### Step 3: Read the "Why This Well" Explanation
For each similar well, there's a plain-English explanation of WHY the system thinks it's similar:
- *"Both wells pass through Hugin Sandstone at similar true depths"*
- *"Formation tops align within 15 meters"*
- *"Well is located 1.2 km away in the same fault block"*

#### Step 4: Check the Formation Tops
The table shows where each rock layer starts:

| Formation | Well F-12 (Current) | Well F-14 (Nearby) | Difference |
|---|---|---|---|
| Nordland Shale | 850m TVDSS | 855m TVDSS | 5m ← Very close! |
| Skade Formation | 2100m TVDSS | 2115m TVDSS | 15m ← Close |
| Hugin Sandstone | 2850m TVDSS | 2870m TVDSS | 20m ← Reasonably close |

> [!TIP]
> **The smaller the depth difference, the more relevant that well's experience is for your current well.**

---

## 🛰️ Page 7: Nearby Wells Radar (radar.html) — FIND WELLS ON A MAP

**URL:** `/radar.html`  
**How to get here:** Click "🛰️ Nearby Wells" from the nav bar

### What You See:
An interactive map showing well locations as dots, with a **distance slider**.

### How to Use It:

1. **Move the slider** — adjust the search radius (1 km to 15 km)
2. **See dots appear on the map** — each dot is a well
3. **Click on a dot** — see that well's details (name, depth, formation info)
4. **The closer the well, the more relevant** its data is for your current location

---

## 🌋 Page 8: 3D Rock Layers (stratigraphy.html)

**URL:** `/stratigraphy.html`  
**How to get here:** Click "🌋 3D Layers" from the nav bar

### What You See:
A visual chart showing rock layers at different depths — like a cross-section of the earth.

### What to Look For:
- **Each colored band** is a different rock layer (formation)
- **The depth labels** show how deep each layer is (in TVDSS — meters below sea level)
- **Well paths** are shown as lines going through the layers
- **Sensor curves** (Gamma Ray, Resistivity) show the rock properties at each depth

---

## ⚡ Page 9: Ahead-of-Bit Hazard Radar (lookahead.html)

**URL:** `/lookahead.html`  
**How to get here:** Click "⚡ Hazard Radar" from the nav bar

### What You See:
A forward-looking danger scanner that shows what's coming in the **next 50-150 meters** ahead of the drill.

### How to Read It:

| Section | What It Shows |
|---|---|
| **Current Bit Position** | Where the drill is right now (depth) |
| **Look-Ahead Window** | The next 50-150 meters — what formations and hazards are expected |
| **Hazard Cards** | Warning cards for specific dangers ahead (e.g., "Lost circulation risk at 2,750m — based on Well F-14 data") |
| **Recommended Mud Weight** | What mud pressure to use to prevent problems |

> [!TIP]
> **This is the most critical page during active drilling.** It tells you what's coming BEFORE you get there.

---

## 📄 Page 10: Document & Report Reader (documents.html)

**URL:** `/documents.html`  
**How to get here:** Click "📄 Report Reader" from the nav bar

### What You See:
A list of all drilling reports (PDFs) that have been loaded into the system.

### What You Can Do:

| Action | How |
|---|---|
| **Browse reports** | Scroll through the list — each report shows well name, date, and type |
| **Search reports** | Use the search box to find reports by well name, date, or keyword |
| **View report details** | Click on a report to see its extracted text and metadata |
| **See the digital fingerprint** | Each report shows its SHA-256 hash — proof it hasn't been tampered with |

### What Gets Uploaded (In Real Deployment):
In a real Oil India deployment, these reports would be:
- **Daily Drilling Reports (DDRs)** — written every day by the rig crew
- **Mud Logs** — records of rock cuttings and gas readings
- **Well Completion Reports** — summary of the entire well after drilling is done
- **Directional Survey Reports** — well path measurements

> [!NOTE]
> **In the demo**, the system comes pre-loaded with **1,759 real Equinor Volve drilling reports** from the North Sea. You don't need to upload anything to test it.

---

## 🤖 Page 11: AI Chat Assistant (copilot.html)

**URL:** `/copilot.html`  
**How to get here:** Click "🤖 AI Chat" from the nav bar

### What You See:
A chat interface — like ChatGPT, but specifically for drilling questions.

### How to Use It:

1. **Type your question** in the text box at the bottom
2. **Press Enter** or click Send
3. **Read the AI's response** — it will include evidence citations

### Example Questions to Try:

| Your Question | What the AI Will Do |
|---|---|
| *"What problems were encountered in the Skade formation?"* | Search all reports for Skade-related incidents and give you a summary with evidence |
| *"What mud weight did well F-14 use at 2800m?"* | Look up the specific mud log data for that well and depth |
| *"Is there a risk of stuck pipe at my current depth?"* | Compare your well's situation with similar past wells and assess risk |
| *"Summarize the drilling history of well NO-15/9-F-12"* | Pull key facts from all reports related to that well |

> [!IMPORTANT]
> **If the AI doesn't have evidence, it will say "I don't have enough verified data to answer this."** This is a SAFETY FEATURE, not a bug. In oil drilling, a wrong answer is more dangerous than no answer.

---

## 📊 Page 12: Blind Well Test (backtest.html)

**URL:** `/backtest.html`  
**How to get here:** Click "📊 Blind Test" from the nav bar

### What You See:
Test results showing how accurately the system predicted real drilling hazards.

### What the Results Mean:

| Metric | What It Means | Our Score |
|---|---|---|
| **Accuracy** | How often the system's warnings were correct | **75%** |
| **Advance Warning Distance** | How far ahead warnings were given | **84 meters** |
| **False Alarm Rate** | How often it warned about something that didn't happen | **80% fewer than basic systems** |
| **Coverage** | How many real incidents it caught | **100% detection** |

### How the Test Works:
1. The system picks a well (e.g., Well F-14)
2. It **hides all of Well F-14's data** from the system
3. It asks: "What dangers will Well F-14 face?"
4. The system can only use data from OTHER wells to predict
5. It then compares the predictions with what actually happened

---

## 🧭 The Navigation Bar — Quick Reference

The nav bar appears on **every page**. Here's what each link does:

| Nav Link | Page It Opens | One-Line Summary |
|---|---|---|
| **★ All Modules** | Scrolls to modules section on landing page | See all features at a glance |
| **⚡ Command Center** | `nexus.html` | Everything combined in one dashboard |
| **📡 Live Rig Monitor** | `pulse.html` | Real-time sensor gauges and alerts |
| **🛡️ Verified AI Search** | `sentinel.html` | Ask questions, get proven answers |
| **⏱️ Time Machine** | `chronos.html` | Replay past drilling operations |
| **💎 Rock Matcher** | `geocore.html` | Compare rock layers between wells |
| **🛰️ Nearby Wells** | `radar.html` | Find wells near a location |
| **🌋 3D Layers** | `stratigraphy.html` | View underground rock cross-sections |
| **⚡ Hazard Radar** | `lookahead.html` | See dangers ahead of the drill |
| **📄 Report Reader** | `documents.html` | Browse uploaded drilling reports |
| **🤖 AI Chat** | `copilot.html` | Chat with the AI assistant |
| **📊 Blind Test** | `backtest.html` | See system accuracy test results |

---

## 🎯 Recommended Order for First-Time Users

If you're opening this for the **first time**, follow this order:

```
Step 1  →  Open the Landing Page (index.html)
            Read the hero section, scroll down to see all modules
            ⬇️
Step 2  →  Click "Launch Command Center" (nexus.html)
            See the big picture — all modules combined
            ⬇️
Step 3  →  Click "Verified AI Search" (sentinel.html)
            Try asking: "What happened in the Skade formation?"
            ⬇️
Step 4  →  Click "Live Rig Monitor" (pulse.html)
            Watch the live sensor gauges — see how they move
            ⬇️
Step 5  →  Click "Time Machine" (chronos.html)
            Select a well, run a replay, watch the predictions
            ⬇️
Step 6  →  Click "Rock Matcher" (geocore.html)
            See which wells have similar underground geology
            ⬇️
Step 7  →  Click "Nearby Wells" (radar.html)
            See all wells on a map with distance slider
            ⬇️
Step 8  →  Click "Hazard Radar" (lookahead.html)
            See what dangers are coming in the next 50-150m
            ⬇️
Step 9  →  Click "AI Chat" (copilot.html)
            Have a conversation about drilling data
            ⬇️
Step 10 →  Click "Blind Test" (backtest.html)
            See the system's accuracy — 75% precision, 84m warning
```

---

## ❓ Common Questions

### "The page is taking forever to load?"
The free Render server goes to sleep after 15 minutes of inactivity. **Wait 20-30 seconds** and it will wake up. This only happens on the first visit.

### "The sensor data isn't moving?"
In demo mode, some data may be static. Try clicking "Start Stream" or "Connect" buttons if they exist. The live sensor feed only works when connected to a real WITSML rig stream.

### "I don't understand what TVDSS means?"
TVDSS = **True Vertical Depth Below Sea Level**. It's the standard way to measure how deep something is underground, no matter what angle the well was drilled at. Think of it as the "real depth" vs. the "pipe length depth."

### "Why does the AI say 'no evidence found'?"
This is intentional! The AI only answers when it has PROOF from real documents. If it can't find proof, it stays silent. **This is a safety feature** — in oil drilling, a wrong guess could cause a blowout.

### "Can I upload my own reports?"
In the full production version (deployed at Oil India), yes. In the demo version, the system is pre-loaded with Equinor Volve field data.

---

<div align="center">

**🛢️ Built for Oil India Limited | Smart India Hackathon 2026**
*Real Evidence. No Guessing. Keeping Drillers Safe.*

**Live Demo:** [https://ertmac-nwis-q4yt.onrender.com/](https://ertmac-nwis-q4yt.onrender.com/)

</div>
