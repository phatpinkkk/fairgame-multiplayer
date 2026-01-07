# FAIRGAME Multiplayer Extension

This repository contains a multiplayer extension of the FAIRGAME framework. The project redesigns the original two-player interaction model to support multi-agent and team-based game-theoretic simulations (e.g., 2v2 and larger groups).

This multiplayer extension was designed and developed during a research program hosted by HCMUT in December 2025, in collaboration with Prof. Thế Anh Hàn (Teesside University, UK).

This work focuses on extending the core game logic, interaction flow, and evaluation mechanisms while preserving the original framework’s goal of analyzing agent behavior in strategic scenarios.

---

## Project Overview

FAIRGAME is a framework for simulating game-theoretic interactions between AI agents.
The original implementation primarily focuses on two-player settings.

This extension introduces:
- Support for **multiple agents per game**
- **Team-based interactions** (e.g., 2v2)
- Generalized payoff handling for more than two players
- Updated game flow and state management for multiplayer scenarios

The goal of this project is to explore how agent behavior, coordination, and outcomes change when moving beyond strictly two-player games.

---

## Key Differences from Original FAIRGAME

Compared to the original FAIRGAME framework, this project includes:

- A redesigned game loop to handle **more than two agents**
- Extended data structures for **multi-agent history and results**
- Support for **team-based configurations**
- Updated validation and processing logic for multiplayer settings
- Additional test cases covering multi-agent scenarios

---

## Project Structure

```text
fairgame-multiplayer/
├── src/                # Core game logic and multiplayer extensions
├── resources/          # Configuration files and game templates
├── unit_tests/         # Unit tests (including multiplayer scenarios)
├── main.py             # Entry point for running simulations
├── api.py              # Optional API interface for interaction/testing
├── requirements.txt    # Python dependencies
├── Dockerfile          # Containerized execution
└── README.md
```

## Getting Started
### Prerequisites
```bash
* Python 3.9+
* pip
```

### Installation
```bash
pip install -r requirements.txt
```

### Running a Simulation
```bash
python main.py
```

Configuration files in the resources/ directory define the game type, number of agents, team structure, and interaction rules.

### Testing

Unit tests are provided to verify both original and multiplayer behavior:
```bash
pytest unit_tests
```

---

## Acknowledgment

This project is based on the FAIRGAME framework developed by the AI Readiness and Assessment (AIRA) group at the Luxembourg Institute of Science and Technology (LIST).

The original FAIRGAME project focuses on two-player game-theoretic simulations for analyzing bias and agent behavior. This repository is an independent extension that redesigns the interaction model to support multiplayer and team-based scenarios.

## License

This project is licensed under the Apache License 2.0, in accordance with the original FAIRGAME framework.
