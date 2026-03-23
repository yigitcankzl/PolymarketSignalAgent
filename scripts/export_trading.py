"""Export trading data for dashboard."""
from engine.trader import Trader

t = Trader()
path = t.export_dashboard_data()
print(f"Trading data exported to {path}")
t.close()
