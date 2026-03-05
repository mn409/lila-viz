import json
import os

print("Loading...")
with open('processed.json') as f:
    data = json.load(f)

print(f"Loaded {len(data)} events")

for e in data:
    e.pop('ts_ms', None)

print("Saving...")
with open('processed.json', 'w') as f:
    json.dump(data, f)

print(f"Done. New size: {os.path.getsize('processed.json')/1024/1024:.1f} MB")