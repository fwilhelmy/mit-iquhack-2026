# MIT iQuHack 2026 – IonQ Challenge Toolkit
Team Blizzards (IQuHACK 2026)

This repository contains our submission for the IonQ challenge at MIT iQuHack 2026.
We were team Blizzards, and our work focuses on the strategy layer of a quantum
entanglement distillation game played on a network graph.

The project combines:
- quantum circuit design for entanglement distillation
- classical decision-making under uncertainty
- budget-aware optimization on a graph

Our main contribution is an adaptive edge-selection strategy that balances
expected reward, probability of success, future expansion potential, and
long-term survivability.

---

## Team

Team Blizzards – IQuHACK 2026  
IonQ Challenge (MIT)

Team members:
- Ismael Gonzalez
- Shane Tendo
- Lukas Rapp
- Félix Wilhelmy
- Aaron Kim

This project was developed collaboratively during MIT iQuHack 2026 as part of
the IonQ challenge, combining quantum circuit intuition with classical
algorithmic strategies under uncertainty and resource constraints. 

---

## Problem Overview

The game is played on a graph-based quantum network.

- Nodes provide rewards:
  - utility qubits
  - bonus Bell pairs
  - limited capacity (competition matters)
- Edges can be claimed by running a quantum distillation circuit
  - each attempt is probabilistic
  - success depends on fidelity exceeding a threshold
  - Bell pairs are only consumed if the claim succeeds

Every move is therefore a risk–reward decision:
high-value nodes are often harder to claim, and overspending Bell pairs can
end the game early.

---

## Strategy Overview

Our strategy evaluates all claimable edges and assigns each an expected value.
At each turn, the edge with the highest expected value is selected.

The score of an edge combines four main components:

1. Immediate node value
   - utility qubits
   - bonus Bell pairs
   - capacity (treated sublinearly to reflect diminishing returns)

2. Future potential (lookahead)
   - approximates the value of nearby nodes unlocked after capture
   - implemented as a discounted 2-hop neighborhood heuristic

3. Distance bias
   - favors expansion near already-owned nodes
   - reduces fragmentation and overextension

4. Probability of success
   - estimates how likely the claim is to succeed
   - learned online from previous attempts

In simplified terms, the strategy optimizes:

(expected node value + future potential) × probability of success

---

## Online Learning: Bandit Model

To estimate probability of success, we use a lightweight multi-armed bandit model.

- Edges are grouped into buckets by difficulty and fidelity threshold
- Each bucket maintains a running estimate of success rate
- Early in the game, the strategy relies on heuristic priors
- As more data is collected, decisions become data-driven

This allows the strategy to adapt dynamically during a game instead of relying
on fixed probabilities.

---

## Budget Safeguards (Implemented)

A key design choice is survivability.

The strategy enforces a strict safeguard:
- it never spends the entire Bell-pair budget
- a small reserve is always kept
- if no edge can be claimed safely, the strategy skips the turn

This prevents catastrophic all-in failures and ensures long-term stability,
even when aggressive heuristics are used.

---

## Aggressive vs Defensive Tradeoff (Future Direction)

The strategy is designed around a tunable risk profile, which can be exposed
as a single aggressiveness slider.

Aggressive behavior:
- prioritizes utility qubits
- expands quickly using heuristics
- accepts higher short-term risk

Defensive behavior:
- prioritizes bonus Bell pairs
- favors high-probability claims
- allocates more Bell pairs per attempt

The budget safeguard remains active in all modes.
This tradeoff is a design direction rather than a fully implemented feature,
but the current scoring weights already support it.

---

## What’s Included

- Game client and session manager for the IonQ challenge API
- Multiple edge-selection strategies (manual, naive, adaptive)
- Adaptive strategy with node scoring, lookahead, and online learning
- Circuit helpers for entanglement distillation
- Visualization tools for graph structure and node scores
- Notebooks and resources used during development

---

## Quick Start

1) Install dependencies

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

2) Run the auto-claim loop

python src/main.py --strategy adaptive

You will be prompted for your player ID and name the first time.
A session.json file is saved locally and reused on subsequent runs.

3) Reset a session (optional)

python src/reset.py

---

## Strategies

Strategies control which edge to claim next:

- dummy: selects nothing (testing and wiring)
- manual: prompts for an edge
- naive: simple heuristic
- adaptive: node scoring, lookahead, and learned success probabilities

New strategies can be added by extending BaseStrategy and wiring them into
src/main.py.

---

## Circuits

The circuits module contains templates for entanglement distillation and a
BaseCircuit interface used by the game loop.

Different circuit variants can adapt Bell-pair usage and distillation type
based on edge difficulty and required fidelity.

---

## Visualization

Two visualization utilities are provided:

- Interactive graph rendering with claimable edges highlighted
- Node score heatmap with owned nodes highlighted

Run the heatmap with:

python src/heatmap.py

---

## Project Layout

.
├── 2026-IonQ-challenge/   Official challenge docs and reference client
├── notebooks/             Experiments and analysis
├── resources/             Reference PDFs
├── src/
│   ├── circuits/          Distillation circuit implementations
│   ├── strategy/          Edge selection strategies
│   ├── utils/             Visualization and helpers
│   ├── client.py          API client
│   ├── game.py            Game helpers and caching
│   ├── main.py            Auto-claim loop
│   ├── heatmap.py         Node score visualization
│   └── reset.py           Session reset utility
├── requirements.txt
└── README.md

---

## Takeaway

This project shows how combining simple heuristics, online learning, and strict
budget control can turn a stochastic quantum networking game into a stable and
adaptive optimization problem.

The strategy is intentionally lightweight, interpretable, and designed to
extend naturally as circuit models and game mechanics evolve.
