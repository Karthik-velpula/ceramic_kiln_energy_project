"""Dependency-free dataset generation fallback used when ML packages are unavailable."""
import csv, math, random
from pathlib import Path

def generate(path, n, seed, version):
    rng = random.Random(seed + version)
    fields = ["pottery_load_kg", "target_temperature_c", "initial_moisture_pct", "planned_duration_hr", "insulation_rating", "kiln_volume_m3", "ambient_temperature_c", "energy_consumption_kwh"]
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader()
        for _ in range(n):
            load=rng.uniform(20,500); temp=rng.uniform(650,1250); moisture=rng.uniform(1,22); duration=rng.uniform(5,24)
            insulation=rng.uniform(.42,.78) if version==1 else rng.uniform(.20,.57)
            volume=rng.uniform(.8,8); ambient=rng.uniform(5,38)
            energy=5.2+.72*load*(temp-ambient)/1000+.31*load*moisture/100+1.8*duration+duration*(1-insulation)*(.55+volume/12)*(temp-ambient)/100
            if version==2: energy*=1.12
            energy=max(.1, energy+rng.gauss(0,3))
            writer.writerow(dict(zip(fields, [load,temp,moisture,duration,insulation,volume,ambient,energy])))

if __name__ == "__main__":
    Path("data").mkdir(exist_ok=True)
    generate("data/kiln_batches_v1.csv",600,42,1)
    generate("data/kiln_batches_v2.csv",600,42,2)
