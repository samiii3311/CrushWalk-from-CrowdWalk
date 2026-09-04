# CrushWalk: Physical Crowd Pressure & Crush Dynamics Addon for CrowdWalk

**CrushWalk** is an experimental physics and telemetry addon for the [CrowdWalk](https://github.com/crest-cassia/CrowdWalk) pedestrian simulation framework. It extends default navigation behavior with realistic physical interaction, side-force pressure accumulation, dynamic bottleneck resistance, and crowd crush/stuck telemetry.

---

## Key Features

* **Physical Force & Side Pressure Modeling:** Extends agent interaction to evaluate physical constraints, bottleneck densities, and force thresholds beyond standard 1D lane progression.


* **Ghost Agent Mechanics:** Manages overlapping and non-colliding agent states (`GhostAgent`, `GhostAgentManager`) to realistically resolve complex bottleneck jams and casualty dynamics.


* **Automated Source Patcher (`patchCrowd.py`):** Automatically injects Java bytecode hooks into CrowdWalk (`AgentBase`, `WalkAgent`, `AgentHandler`, `BasicSimulationLauncher`), adds `DynamicAgentLogger.java`, and recompiles the core engine.


* **Comprehensive Telemetry & Logging:** Logs granular agent data (speed, force, link ID, nodes, timestamps, and crushed states) via `TelemetryHandler.rb` and `DynamicAgentLogger`.


* **GPS Data Integration (`gpxToCsv.py`):** Converts real-world GPX trace logs into CrowdWalk-compatible CSV coordinate datasets for empirical trajectory validation.


* **Extensive Benchmark Suite (`CrushTesting/`):** Pre-configured test scenarios for one-way corridors, turns, narrow entrances, wide exits, busy paths, 2-way crossroads, 4-way crossroads, and random motion.



---

## Repository Structure

```text
CrushWalk/
├── Crush2/              # Intermediate Ruby-agent prototype and scenarios[cite: 1]
├── Crush3/              # Advanced blackboard architecture & physics tests[cite: 1]
├── CrushTest/           # Standard integration test setup and plotting utilities[cite: 1]
├── CrushTesting/        # Comprehensive benchmark maps & XML topologies:[cite: 1]
│   ├── 1OneWay.xml      # Single-direction bottleneck corridor[cite: 1]
│   ├── 2Turn.xml        # Sharp turn bottleneck[cite: 1]
│   ├── 3SmallEnter.xml  # Funnel/narrow entrance topology[cite: 1]
│   ├── 4BigExit.xml     # Constrained entry with wide dissipation exit[cite: 1]
│   ├── 5BusyPath.xml    # Bidirectional high-density pathway[cite: 1]
│   ├── 6Crossroad2way.xml # 2-way intersecting corridor[cite: 1]
│   └── 7Crossroad4way.xml # 4-way intersection gridlock test[cite: 1]
├── Test/                # Real-world test maps (e.g., HigashiKU) & generation configs[cite: 1]
├── patchCrowd.py        # Automated Java hook injector and Gradle builder[cite: 1]
├── run.py               # Batch execution runner[cite: 1]
└── gpxToCsv.py          # GPX trace parser to CrowdWalk CSV format[cite: 1]

```

---

## Getting Started

### Prerequisites

* **Java JDK:** OpenJDK / Oracle JDK 17+ (or 21+)
* **Python:** 3.8+
* **JRuby / Ruby:** Embedded with CrowdWalk
* **CrowdWalk:** Cloned and accessible locally

### Installation & Patching

1. Place the `CrushWalk` files in your workspace or inside your CrowdWalk repository.


2. Run the patcher script to inject custom hooks into CrowdWalk's Java source code and rebuild the project:


```bash
python patchCrowd.py

```


This automatically locates CrowdWalk files, generates `DynamicAgentLogger.java`, modifies agent collision rules, adjusts the simulation exit condition, fixes launcher scripts, and executes `./gradlew build -x test`.



---

## Running Simulations

### Running a Single Experiment

Execute any benchmark configuration using CrowdWalk's launcher:

```bash
# Example: Run CrushTesting Benchmark
sh quickstart.sh ./CrushTesting/prop.json -g2

```

### Running Batch Automation

Use the batch controller script to run multiple parameter sweeps:

```bash
python run.py

```

### Processing GPX Field Data

Convert empirical GPS tracker traces to model coordinates:

```bash
python gpxToCsv.py input_track.gpx output_coordinates.csv

```

---

## Telemetry Output

The addon logs agent metrics to CSV for analysis:

* `log_crushed_agents.csv`: Timestamps, agent IDs, and coordinates where physical crush thresholds were breached.


* `dynamic_metrics.csv`: Real-time agent status, link occupations, exposure, and custom agent tags across every simulation tick.


# Notes
*Work in Progress: This repository is actively under development as of September 4th 2026.

*AI Assistance: Portions of the code and documentation in this repository were developed with AI assistance.
