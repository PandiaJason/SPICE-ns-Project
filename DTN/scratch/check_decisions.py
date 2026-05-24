import json

with open("/home/jason/DTN/results/contact_plan.json", "r") as f:
    contacts = json.load(f)

ss_dsn_contacts = [c for c in contacts if c["source"] == 1 and c["dest"] == 3]
print(f"Total SmallSat -> DSN contacts: {len(ss_dsn_contacts)}")
for c in ss_dsn_contacts:
    print(f"  Start: {c['start_time']:.1f}, End: {c['end_time']:.1f}, Duration: {c['duration_s']:.1f}, Capacity: {c['capacity_MB']:.1f} MB, Rate: {c['data_rate_bps']/1e3:.1f} kbps")
