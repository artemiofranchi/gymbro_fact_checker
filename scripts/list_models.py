"""List models available on Nebius Token Factory (NVIDIA ones first). Put chosen ids into .env."""
from gymbro.llm import client

ids = sorted(m.id for m in client().models.list().data)
nv = [i for i in ids if "nvidia" in i.lower() or "nemotron" in i.lower()]
print("NVIDIA / Nemotron models:")
for i in nv:
    print("  ", i)
print(f"\n{len(ids)} models total")
