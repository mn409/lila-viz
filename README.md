# LILA BLACK — Player Journey Visualizer

A web-based tool built for the LILA Games Level Design team to explore player behavior across maps using 5 days of production telemetry data from LILA BLACK.

**Live App:** https://lila-viz-muurcync7lfw3xggxazvsb.streamlit.app

---

## What It Does

Level Designers can open this tool in their browser and immediately see where players are moving, fighting, looting, and dying — across all three maps and five days of real match data. No data science background required.

### Features

- **Player Journey Map** — All movement and event data plotted on the correct minimap with accurate world-to-pixel coordinate mapping
- **Human vs Bot distinction** — Human players (UUID identifiers) and bots (numeric IDs) rendered with separate colors and toggles
- **Event Type Markers** — 8 event types rendered as distinct markers: Movement, Bot Movement, Kill, Death, Bot Kill, Bot Death, Storm Death, and Loot
- **Filters** — Filter by map, date range, and individual match
- **Match Timeline** — Scrub through a match event-by-event to watch it unfold. Drag the slider or use arrow keys for precise control
- **Heatmap Overlays** — Three modes: Traffic (where players spend time), Kills, and Deaths
- **Stats Panel** — Live metrics including total events, kill/death counts, storm deaths, loot pickups, and human vs bot breakdown

---

## Running Locally

### Prerequisites
- Python 3.11+
- The `player_data/` folder with raw `.nakama-0` parquet files (not included in repo)

### Setup

```bash
git clone https://github.com/mn409/lila-viz.git
cd lila-viz
pip install -r requirements.txt
```

### Generate Processed Data

```bash
python preprocess.py
```

This reads all 1,243 parquet files from `player_data/`, decodes event bytes, converts world coordinates to minimap pixels, detects human vs bot players, and outputs `processed.json` (~19MB).

### Run the App

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## Project Structure

```
lila-viz/
├── app.py              # Main Streamlit application
├── preprocess.py       # Data pipeline: parquet → processed.json
├── processed.json      # Pre-processed event data (committed for deployment)
├── requirements.txt    # Python dependencies
├── minimaps/           # Minimap images for all 3 maps
│   ├── AmbroseValley_Minimap.png
│   ├── GrandRift_Minimap.png
│   └── Lockdown_Minimap.png
└── player_data/        # Raw .nakama-0 parquet files (not committed, 1243 files)
```

---

## Data

| Stat | Value |
|------|-------|
| Total events | 89,104 |
| Date range | Feb 10–14, 2026 |
| Maps | AmbroseValley (69%), Lockdown (24%), GrandRift (7%) |
| Human events | 66,161 (74%) |
| Bot events | 22,943 (26%) |
| Human kills | 3 |
| Bot kills | 2,415 |
| Storm deaths | 39 |

### Key Insight

Only 3 human-vs-human kills across 5 days of data suggests players are primarily engaging with bots rather than each other. Combined with GrandRift's low traffic (7%), this points to either spawn distribution issues or players actively avoiding conflict on that map.

---

## Coordinate Mapping

World coordinates are converted to minimap pixels using:

```
u = (x - origin_x) / scale
v = (z - origin_z) / scale
pixel_x = u * image_width
pixel_y = (1 - v) * image_height   # Y-axis flipped (image origin top-left)
```

Map configs:

| Map | Scale | Origin X | Origin Z |
|-----|-------|----------|----------|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

---

## Tech Stack

- **Python + Streamlit** — Fast to build, no frontend complexity, parquet support out of the box
- **Pillow** — Image rendering and alpha compositing for event overlays
- **SciPy** — Gaussian blur for smooth heatmap generation
- **Streamlit Cloud** — Free hosting, auto-deploys on every GitHub push

---

## Architecture

See the [Architecture Doc](https://docs.google.com/document/d/architecture) for full decisions, trade-offs, and what I'd do differently with more time.
