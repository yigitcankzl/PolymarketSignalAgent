"""Test cross-platform arbitrage with event verification."""
from engine.synthesis_client import SynthesisClient

c = SynthesisClient()
arbs = c.detect_arbitrage(min_price_diff=0.02)

print(f"\n=== {len(arbs)} verified cross-platform arbitrage opportunities ===\n")
for a in arbs[:15]:
    print(f"  {a['polymarket']['outcome']}: PM={a['polymarket']['yes_price']:.1%} vs KA={a['kalshi']['yes_price']:.1%} | +{a['profit_potential_pct']:.1f}%")
    print(f"    PM: {a['polymarket']['event'][:45]}")
    print(f"    KA: {a['kalshi']['event'][:45]}")
    print(f"    {a['action']} | similarity={a['event_similarity']}")
    print(f"    {a.get('synthesis_url', '')}")
    print()

c.close()
