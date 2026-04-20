# 🏎️ Entelect Grand Prix — Race Strategy Optimiser

**Team: Byte Me** | Entelect University Cup Hackathon | April 2026

A Python-based race strategy optimisation engine built for the [Entelect Grand Prix](https://entelect.co.za/) hackathon challenge. Given a JSON level file describing the car, track, tyres, fuel, and weather, the program automatically generates the optimal race strategy to minimise lap time and maximise score.

---

## 📋 Problem Overview

The challenge requires building a program that acts as an F1 race strategist, deciding:

- Which tyre compound to start on
- Target speed and braking point for each straight
- When to pit for tyre changes and/or refuelling
- How to adapt to changing weather conditions and tyre degradation

Strategies are evaluated across four levels of increasing complexity — from basic track navigation through to full tyre degradation and weather management.

---

## 🧠 Approach

The solution uses a **grid search optimisation** algorithm over the key strategic variables:

- Initial tyre selection
- Pit stop timing and frequency
- Fuel refuel amounts per stop

For each candidate strategy, a full race simulation is run using the physics model defined in the problem specification. The simulation scores the result and the best-performing strategy is saved as the submission.

Fuel needs are estimated by running a sample lap before the search begins, allowing pit stop configurations to be generated dynamically based on actual race requirements rather than hardcoded assumptions.

---

## 🗂️ Project Structure

```
├── f1_race_strategy.py   # Main solver — simulation engine + optimiser
├── 1.txt                 # Level 1 JSON input
├── 2.txt                 # Level 2 JSON input
├── 3.txt                 # Level 3 JSON input
├── 4.txt                 # Level 4 JSON input
└── submission.txt        # Generated race strategy output
```

---

## ⚙️ How It Works

### Physics Simulation

The `RaceSimulator` class models each track segment according to the official rules:

- **Straights**: Three phases — acceleration, cruise, braking — each with time, fuel, and tyre wear calculated using the problem's kinematics formulas.
- **Corners**: Entry speed checked against the maximum safe corner speed (`sqrt(friction × g × radius) + crawl_constant`). Exceeding it triggers crash penalties and crawl mode.
- **Tyre friction**: Degrades over time based on compound, weather, and segment type (straight, braking, corner).
- **Fuel consumption**: Calculated per segment using the drag-based formula from the spec.
- **Limp/Crawl mode**: Triggered by tyre blowouts, fuel depletion, or corner crashes.

### Optimisation

The `RaceOptimizer` class runs a grid search across tyre and pit stop combinations:

1. Estimates fuel consumption per lap via a sample simulation.
2. Calculates the minimum number of pit stops required to cover fuel needs.
3. Generates evenly-spaced pit stop configurations from that minimum upward.
4. Scores each strategy using the Level 1–4 scoring formulas.
5. Returns the highest-scoring valid strategy.

---

## 🚀 Running the Solver

### Requirements

- Python 3.8+
- No external dependencies — standard library only

### Usage

```bash
python f1_race_strategy.py <level_file>
```

**Example:**

```bash
python f1_race_strategy.py 1.txt
```

The program will print iteration-by-iteration progress and write the best strategy to `submission.txt`.

---

## 📤 Output Format

The output is a JSON file describing the full race strategy, for example:

```json
{
  "initial_tyre_id": 1,
  "laps": [
    {
      "lap": 1,
      "segments": [
        { "id": 1, "type": "straight", "target_m/s": 72, "brake_start_m_before_next": 595 },
        { "id": 2, "type": "corner" }
      ],
      "pit": { "enter": false }
    }
  ]
}
```

---

## 📊 Scoring

| Level | Formula |
|-------|---------|
| 1 | `500,000 × (time_reference / time)³` |
| 2 & 3 | Base score + fuel efficiency bonus |
| 4 | Base score + fuel bonus + tyre usage bonus |

---

## 🏁 Levels

| Level | Focus |
|-------|-------|
| 1 | Track navigation, tyre selection, braking points |
| 2 | Fuel management, pit stops |
| 3 | Weather conditions, tyre compound switching |
| 4 | Tyre degradation, blowout avoidance, tyre efficiency scoring |
