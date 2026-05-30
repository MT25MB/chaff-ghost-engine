# ⚡ CHAFF Ghost Engine

> Phase 1 of Project CHAFF — Synthetic privacy noise generation.

A Python engine that generates realistic synthetic Reddit personas with human-like behavioral patterns. Each ghost is derived deterministically from a cryptographic seed — no database needed, fully reproducible.

**Part of [Project CHAFF](https://github.com/MT25MB/chaff-extension)**

---

## ⚡ Quick Start (Windows)

```batch
1. Install Python from https://python.org (check "Add to PATH")
2. Double-click install.bat
3. Double-click run_dry.bat
```

## Quick Start (Mac/Linux)

```bash
pip3 install -r requirements.txt
chmod +x run_dry.sh && ./run_dry.sh
```

---

## What It Does

The Ghost Engine generates synthetic Reddit users with:

- **Deterministic identity** — same seed always produces the same ghost (name, age, location, personality, interests)
- **Big Five personality model** — extraversion determines posting frequency, agreeableness affects tone, neuroticism creates emotional variability
- **Human behavioral timing** — circadian rhythms, peak hours, silence days, binge periods
- **Local LLM content** — uses Ollama (free, runs on your machine) to generate contextual comments and posts in the ghost's voice
- **Ghost archetypes** — pre-built personality templates (lurker, commenter, power_user, etc.)
- **Upvote behavior** — ghosts upvote posts when browsing, varying by archetype
- **Seasonal awareness** — ghosts reference current season and recent holidays
- **Activity logging** — all actions saved to JSON files for analysis
- **Profile export/import** — save and load ghost profiles across sessions
- **Bulk health monitoring** — check multiple accounts for shadowbans at once
- **Detection monitoring** — checks for shadowbans and feeds evasion intelligence

## Usage

```bash
# Show a ghost profile (dry run — nothing posted)
python ghost_engine.py --dry-run

# Generate 3 different ghosts and show all profiles
python ghost_engine.py --count 3 --dry-run

# Use a specific seed (same seed = same ghost every time)
python ghost_engine.py --seed my_seed_42 --dry-run

# Use an archetype for consistent behavior
python ghost_engine.py --archetype lurker --count 5 --dry-run

# Run one simulated activity cycle
python ghost_engine.py --seed my_seed_42 --run-once --dry-run

# Check if a Reddit account is shadowbanned
python ghost_engine.py --check-health reddit_username

# Check multiple accounts at once
python ghost_engine.py --check-health-batch usernames.txt

# Export ghost profiles to JSON
python ghost_engine.py --count 5 --export-profiles ghosts.json

# Import ghost profiles from JSON
python ghost_engine.py --import-profiles ghosts.json --run-once

# View activity stats
python ghost_engine.py --stats

# View stats for a specific ghost
python ghost_engine.py --stats-ghost username_here

# Live mode (requires Reddit API credentials in config.json)
python ghost_engine.py --seed my_seed_42 --live --run-continuous
```

## Ghost Archetypes

Archetypes define consistent behavioral patterns:

| Archetype | Description | Posts/Day | Comment Ratio | Upvote Rate |
|-----------|-------------|-----------|---------------|-------------|
| `lurker` | Mostly reads, rarely posts | 0.3x | 10% | 80% |
| `commenter` | Frequent comments, rare posts | 0.5x | 90% | 50% |
| `power_user` | Very active, posts frequently | 2.0x | 60% | 30% |
| `newcomer` | Tentative, asks questions | 0.7x | 70% | 60% |
| `veteran` | Experienced, gives advice | 0.8x | 70% | 40% |
| `troll` | Contrarian, stirs discussion | 1.5x | 80% | 10% |
| `helpful` | Friendly, shares knowledge | 0.6x | 80% | 70% |
| `casual` | Balanced, normal behavior | 1.0x | 60% | 50% |

## Setting Up Live Mode (Optional)

To actually post to Reddit, you need Reddit API credentials:

1. Create a fresh Reddit account (use a temp email)
2. Go to https://www.reddit.com/prefs/apps
3. Click "Create App" → select "script"
4. Copy `config.example.json` to `config.json`
5. Fill in your client_id, client_secret, username, password
6. Run: `python ghost_engine.py --live --run-once`

**Never commit config.json to git** — it contains credentials.

## Architecture

```
ghost_engine.py
├── GhostGenerator      — Deterministic identity from seed
├── ContentGenerator    — Local LLM (Ollama) content creation
├── BehaviorScheduler   — Human-realistic timing engine
├── GhostAgent          — Per-ghost orchestrator
├── GhostNetwork        — Multi-ghost coordinator
├── DetectionMonitor    — Shadowban health checks
├── ActivityLogger      — Persistent JSON action logs
├── SeasonalContext     — Season/holiday awareness
└── GhostArchetype      — Pre-built personality templates
```

## Roadmap

- [ ] P2P seed distribution via libp2p (Phase 2)
- [ ] Multi-platform support: Twitter/X, Nextdoor, forums (Phase 3)
- [ ] Cross-platform contradiction engine (Phase 3)
- [ ] Adversarial red-team detection engine (Phase 4)
- [ ] Ghost social graph simulation (Phase 4)

## Legal

This is privacy research software. See [LEGAL.md](https://github.com/MT25MB/chaff-extension/blob/main/LEGAL.md) for full analysis.

## Contributing

PRs welcome. This is open source under GPL-3.0.

---
*Project CHAFF · github.com/MT25MB · GPL-3.0*
