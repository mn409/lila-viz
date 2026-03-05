import streamlit as st
import json
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LILA BLACK — Map Visualizer",
    page_icon="🎮",
    layout="wide"
)

# ─── Event Visual Style ───────────────────────────────────────────────────────
EVENT_STYLE = {
    'Position':      {'color': (100, 180, 255, 120), 'size': 3,  'label': '🔵 Movement'},
    'BotPosition':   {'color': (150, 150, 150, 80),  'size': 2,  'label': '⚪ Bot Movement'},
    'Kill':          {'color': (255, 50,  50,  255), 'size': 8,  'label': '🔴 Kill (Human)'},
    'Killed':        {'color': (255, 150, 0,   255), 'size': 8,  'label': '🟠 Death (Human)'},
    'BotKill':       {'color': (255, 220, 0,   255), 'size': 6,  'label': '🟡 Bot Killed'},
    'BotKilled':     {'color': (200, 100, 255, 255), 'size': 6,  'label': '🟣 Killed by Bot'},
    'KilledByStorm': {'color': (0,   255, 200, 255), 'size': 10, 'label': '🟢 Storm Death'},
    'Loot':          {'color': (255, 255, 255, 180), 'size': 4,  'label': '⚪ Loot'},
}

MINIMAP_PATHS = {
    'AmbroseValley': 'minimaps/AmbroseValley_Minimap.png',
    'GrandRift':     'minimaps/GrandRift_Minimap.png',
    'Lockdown':      'minimaps/Lockdown_Minimap.png',
}

# ─── Load Data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open('processed.json', 'r') as f:
        data = json.load(f)
    return data

# ─── Filter Data ──────────────────────────────────────────────────────────────
def filter_data(data, selected_map, selected_dates,
                selected_match, show_humans, show_bots):
    filtered = [
        e for e in data
        if e['map_id'] == selected_map
        and e['date'] in selected_dates
    ]
    if selected_match != 'All Matches':
        filtered = [e for e in filtered if e['match_id'] == selected_match]
    if not show_humans:
        filtered = [e for e in filtered if e['player_type'] != 'human']
    if not show_bots:
        filtered = [e for e in filtered if e['player_type'] != 'bot']
    return filtered

# ─── Draw Events on Map ───────────────────────────────────────────────────────
def draw_events(img, events, show_events):
    base = img.convert('RGBA')
    overlay = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for ev in events:
        event_type = ev['event']
        if event_type not in show_events:
            continue
        style = EVENT_STYLE.get(event_type, {'color': (255, 255, 255, 180), 'size': 3})
        px, py = int(ev['px']), int(ev['py'])
        s = style['size']
        draw.ellipse([px-s, py-s, px+s, py+s], fill=style['color'])
    return Image.alpha_composite(base, overlay)

# ─── Draw Heatmap ─────────────────────────────────────────────────────────────
def draw_heatmap(img, events, heatmap_type):
    base = img.convert('RGBA')
    size_w, size_h = base.size

    event_map = {
        'traffic': ('Position', 'BotPosition'),
        'kills':   ('Kill', 'BotKill'),
        'deaths':  ('Killed', 'BotKilled', 'KilledByStorm'),
    }
    target_events = event_map.get(heatmap_type, ())

    grid = np.zeros((size_h, size_w), dtype=np.float32)

    for ev in events:
        if ev['event'] in target_events:
            x, y = int(ev['px']), int(ev['py'])
            if 0 <= x < size_w and 0 <= y < size_h:
                grid[y][x] += 1

    if grid.max() == 0:
        st.warning(f"No {heatmap_type} events found for current filters.")
        return base

    grid = gaussian_filter(grid, sigma=20)
    grid = grid / grid.max()

    heatmap_arr = np.zeros((size_h, size_w, 4), dtype=np.uint8)
    heatmap_arr[..., 0] = (grid * 255).astype(np.uint8)
    heatmap_arr[..., 1] = ((1 - grid) * 100).astype(np.uint8)
    heatmap_arr[..., 2] = 50
    heatmap_arr[..., 3] = (grid * 200).astype(np.uint8)

    heat_img = Image.fromarray(heatmap_arr, 'RGBA')
    return Image.alpha_composite(base, heat_img)

# ─── Stats Panel ──────────────────────────────────────────────────────────────
def show_stats(events):
    if not events:
        st.warning("No events match current filters.")
        return

    total = len(events)
    humans = sum(1 for e in events if e['player_type'] == 'human')
    bots = sum(1 for e in events if e['player_type'] == 'bot')
    kills = sum(1 for e in events if e['event'] in ('Kill', 'BotKill'))
    deaths = sum(1 for e in events if e['event'] in ('Killed', 'BotKilled', 'KilledByStorm'))
    storm_deaths = sum(1 for e in events if e['event'] == 'KilledByStorm')
    loot = sum(1 for e in events if e['event'] == 'Loot')

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Events", f"{total:,}")
    c2.metric("Kills", f"{kills:,}")
    c3.metric("Deaths", f"{deaths:,}")
    c4.metric("Storm Deaths", f"{storm_deaths:,}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Loot Pickups", f"{loot:,}")
    c6.metric("Human Events", f"{humans:,}")
    c7.metric("Bot Events", f"{bots:,}")
    c8.metric("Human %", f"{humans/total*100:.0f}%")

# ─── Main App ─────────────────────────────────────────────────────────────────
def main():
    st.title("🎮 LILA BLACK — Player Journey Visualizer")
    st.caption("Built for the Level Design team to explore player behavior across maps.")

    try:
        with st.spinner("Loading match data..."):
            raw_data = load_data()
    except FileNotFoundError:
        st.error("processed.json not found. Please run preprocess.py first.")
        st.code("python preprocess.py")
        return

    # ── Sidebar Filters ──────────────────────────────────────────────────────
    st.sidebar.title("🗺️ Filters")

    maps = sorted(set(e['map_id'] for e in raw_data))
    default_map_idx = maps.index('AmbroseValley') if 'AmbroseValley' in maps else 0
    selected_map = st.sidebar.selectbox("Map", maps, index=default_map_idx)

    all_dates = sorted(set(
        e['date'] for e in raw_data if e['map_id'] == selected_map
    ))
    selected_dates = st.sidebar.multiselect("Date", all_dates, default=all_dates)

    if not selected_dates:
        st.warning("Please select at least one date.")
        return

    pre_filtered = [
        e for e in raw_data
        if e['map_id'] == selected_map and e['date'] in selected_dates
    ]
    matches = sorted(set(e['match_id'] for e in pre_filtered))
    selected_match = st.sidebar.selectbox("Match", ['All Matches'] + matches)

    st.sidebar.markdown("---")
    show_humans = st.sidebar.checkbox("Show Human Players", value=True)
    show_bots = st.sidebar.checkbox("Show Bots", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Event Types**")
    show_events = set()
    for event_type, style in EVENT_STYLE.items():
        if st.sidebar.checkbox(style['label'], value=True, key=f"ev_{event_type}"):
            show_events.add(event_type)

    st.sidebar.markdown("---")
    heatmap_mode = st.sidebar.radio(
        "Heatmap Overlay",
        ["None", "Traffic", "Kills", "Deaths"]
    )

    # ── Apply Filters ────────────────────────────────────────────────────────
    filtered = filter_data(
        raw_data,
        selected_map,
        selected_dates,
        selected_match,
        show_humans,
        show_bots
    )

    # ── Timeline Slider ──────────────────────────────────────────────────────
    if selected_match != 'All Matches' and filtered:
        max_seq = max(e.get('seq', 0) for e in filtered)

        if max_seq > 0:
            st.markdown("### ⏱️ Match Timeline")
            col_progress, col_slider = st.columns([1, 5])

            with col_slider:
                seq_cutoff = st.slider(
                    "Drag to replay match",
                    min_value=0,
                    max_value=int(max_seq),
                    value=int(max_seq),
                    label_visibility="collapsed"
                )

            progress = seq_cutoff / max_seq * 100
            col_progress.metric("Progress", f"{progress:.0f}%")
            filtered = [e for e in filtered if e.get('seq', 0) <= seq_cutoff]
            st.caption(f"Showing {len(filtered):,} of {max_seq+1} events in this match.")
        else:
            st.info("⏱️ Timeline: Select a specific match to enable playback.")

    # ── Stats Panel ──────────────────────────────────────────────────────────
    st.markdown("### 📊 Match Statistics")
    show_stats(filtered)
    st.markdown("---")

    # ── Map Display ──────────────────────────────────────────────────────────
    matches_shown = (
        selected_match if selected_match != 'All Matches'
        else f"{len(matches)} matches"
    )
    st.markdown(f"### {selected_map} — {len(filtered):,} events — {matches_shown}")

    img = Image.open(MINIMAP_PATHS[selected_map])

    if heatmap_mode != "None":
        result_img = draw_heatmap(img, filtered, heatmap_mode.lower())
    else:
        result_img = draw_events(img, filtered, show_events)

    st.image(result_img, width=900)

    # ── Legend ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**Legend**")
    cols = st.columns(4)
    for i, (_, style) in enumerate(EVENT_STYLE.items()):
        cols[i % 4].markdown(style['label'])

    st.markdown("---")
    st.caption("LILA BLACK Player Journey Visualizer — Built for the Level Design Team")

if __name__ == "__main__":
    main()