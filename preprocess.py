import os
import json
import pandas as pd
from pathlib import Path

# ─── Map Configuration ────────────────────────────────────────────────────────
MAP_CONFIG = {
    'AmbroseValley': {'scale': 900,  'origin_x': -370, 'origin_z': -473},
    'GrandRift':     {'scale': 581,  'origin_x': -290, 'origin_z': -290},
    'Lockdown':      {'scale': 1000, 'origin_x': -500, 'origin_z': -500},
}

# ─── Coordinate Conversion ────────────────────────────────────────────────────
def world_to_pixel(x, z, map_name):
    c = MAP_CONFIG[map_name]
    u = (x - c['origin_x']) / c['scale']
    v = (z - c['origin_z']) / c['scale']
    return round(u * 1024), round((1 - v) * 1024)

# ─── Human vs Bot Detection ───────────────────────────────────────────────────
def is_human(user_id):
    return '-' in str(user_id)

# ─── Process All Files ────────────────────────────────────────────────────────
def process_all(data_root="player_data"):
    all_events = []
    days = ['February_10', 'February_11', 'February_12', 'February_13', 'February_14']

    for day in days:
        day_path = Path(data_root) / day
        if not day_path.exists():
            print(f"Skipping {day} - folder not found")
            continue

        files = list(day_path.iterdir())
        print(f"Processing {day}: {len(files)} files...")

        for filepath in files:
            try:
                df = pd.read_parquet(filepath)

                # Decode event bytes to string
                df['event'] = df['event'].apply(
                    lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x)
                )

                # Add metadata columns
                df['date'] = day
                df['player_type'] = df['user_id'].apply(
                    lambda x: 'human' if is_human(x) else 'bot'
                )

                # Convert coordinates to pixel positions
                map_name = df['map_id'].iloc[0]
                if map_name not in MAP_CONFIG:
                    continue

                df['px'] = df.apply(
                    lambda row: world_to_pixel(row['x'], row['z'], map_name)[0], axis=1
                )
                df['py'] = df.apply(
                    lambda row: world_to_pixel(row['x'], row['z'], map_name)[1], axis=1
                )

                # Convert timestamp to milliseconds integer for JSON
                df['ts_ms'] = pd.to_datetime(df['ts']).astype('int64') // 1_000_000

                # Keep only what we need
                keep = ['user_id', 'match_id', 'map_id', 'date',
                        'player_type', 'event', 'px', 'py', 'ts_ms']
                df = df[keep]

                all_events.append(df)

            except Exception as e:
                print(f"  Error reading {filepath.name}: {e}")
                continue

    # Combine everything
    print("\nCombining all data...")
    combined = pd.concat(all_events, ignore_index=True)

    # Clean up match_id (remove .nakama-0 suffix)
    combined['match_id'] = combined['match_id'].str.replace('.nakama-0', '', regex=False)

    print(f"Total events: {len(combined):,}")
    print(f"Maps: {combined['map_id'].value_counts().to_dict()}")
    print(f"Player types: {combined['player_type'].value_counts().to_dict()}")
    print(f"Event types: {combined['event'].value_counts().to_dict()}")

    # Save to JSON
    output = combined.to_dict(orient='records')
    with open('processed.json', 'w') as f:
        json.dump(output, f)

    print(f"\nSaved processed.json ({os.path.getsize('processed.json') / 1024 / 1024:.1f} MB)")
    return combined

if __name__ == "__main__":
    process_all()