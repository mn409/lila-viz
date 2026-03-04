import pandas as pd

df = pd.read_parquet("player_data/February_10/0b260629-9386-49d6-a66b-91ccbd3a4abc_3002eeae-28b4-40ca-8089-2ce1ec603642.nakama-0")

df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else x)

print(df.head(10))
print("\nEvent types:", df['event'].value_counts().to_dict())
print("\nMap:", df['map_id'].iloc[0])
print("\nTotal rows:", len(df))

def world_to_pixel(x, z, map_name):
    config = {
        'AmbroseValley': {'scale': 900,  'origin_x': -370, 'origin_z': -473},
        'GrandRift':     {'scale': 581,  'origin_x': -290, 'origin_z': -290},
        'Lockdown':      {'scale': 1000, 'origin_x': -500, 'origin_z': -500},
    }
    c = config[map_name]
    u = (x - c['origin_x']) / c['scale']
    v = (z - c['origin_z']) / c['scale']
    pixel_x = u * 1024
    pixel_y = (1 - v) * 1024
    return round(pixel_x), round(pixel_y)

# Test with README example
px, py = world_to_pixel(-301.45, -355.55, 'AmbroseValley')
print(f"Pixel position: ({px}, {py})")
print(f"Expected:       (78, 890)")
print(f"Match: {px == 78 and py == 890}")