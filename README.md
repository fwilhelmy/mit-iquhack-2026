# MIT iQuHack 2026 – IonQ Challenge Toolkit

This repository contains a Python client, strategies, and circuit tooling for the iQuHack 2026 IonQ Quantum Entanglement Distillation challenge. It wraps the official challenge API with higher-level helpers, provides multiple edge-claiming strategies, and includes utilities for visualization and analysis of the game graph.

## What’s Included

- **Game client + session manager** to register, resume sessions, and talk to the challenge API.
- **Strategies** for selecting edges (manual, naive, adaptive, blacklist wrapper).
- **Circuit helpers** for distillation attempts (including Shane/Aaron circuit variants).
- **Visualization tools** for graph views and node score heatmaps.
- **Notebooks + resources** for experimentation and reference material.

## Quick Start

### 1) Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the Auto-Claim Loop

```bash
python src/main.py --strategy adaptive
```

You’ll be prompted for your player ID and name the first time. A `session.json` file is saved locally and reused on subsequent runs. The loop attempts to claim edges continuously and writes a `claim_attempts.csv` log at exit.

### 3) Reset a Session (Optional)

```bash
python src/reset.py
```

This calls the server restart endpoint and prompts you to choose a new starting node.

## Strategies

Strategies control which edge to claim next:

- `dummy`: selects nothing (useful for wiring/testing).
- `manual`: prompts for an edge.
- `naive`: simple heuristic for claimable edges.
- `adaptive`: uses node scoring and edge heuristics.

You can add your own strategy by extending `BaseStrategy` and wiring it into `src/main.py`.

## Circuits

The `circuits/` module includes circuit templates for entanglement distillation and a `BaseCircuit` interface used by the game loop. `ShaneCircuit` includes heuristics to vary Bell pairs and distillation type based on edge difficulty.

## Visualization

Two visualization entry points are provided:

- `GraphTool` (`src/utils/visualization.py`): interactive graph rendering with claimable edges highlighted.
- `heatmap.py`: draws a node score heatmap with owned nodes highlighted in red.

Run the heatmap utility with:

```bash
python src/heatmap.py
```

## Project Layout

```
.
├── 2026-IonQ-challenge/   # Official challenge docs, demo notebooks, and reference client
├── notebooks/             # Local experiments
├── resources/             # Reference PDFs
├── src/
│   ├── circuits/          # Distillation circuit implementations
│   ├── strategy/          # Edge selection strategies
│   ├── utils/             # Visualization + Discord hooks
│   ├── client.py          # API client
│   ├── game.py            # Game helpers and caching
│   ├── main.py            # Auto-claim loop entry point
│   ├── heatmap.py         # Score heatmap rendering
│   └── reset.py           # Reset and re-select starting node
├── requirements.txt
└── README.md
```

## Notes

- The API base URL is defined in `src/client.py`. If the challenge endpoint changes, update it there or adjust your local `session.json`.
- Claim attempts are logged to `claim_attempts.csv` when `src/main.py` exits.

For the original challenge README and API reference, see `2026-IonQ-challenge/README.md`.
