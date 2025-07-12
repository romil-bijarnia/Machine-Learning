"""Run a 30‑day supermarket simulation with learning customer agents."""

import datetime as dt
import random
import pprint

from store_ai import StoreAI, CustomerAgent

# --------------------------------------------------------------------- #
# 1. Static catalogue definition                                        #
# --------------------------------------------------------------------- #
catalogue = {
    "bread": {"case": 20, "lead": 2, "safety": 15, "cost": 1.2, "price": 2.5},
    "milk":  {"case": 12, "lead": 1, "safety": 10, "cost": 0.6, "price": 1.5},
    "eggs":  {"case": 30, "lead": 3, "safety": 25, "cost": 2.0, "price": 3.5},
}

# --------------------------------------------------------------------- #
# 2. Run simulation                                                     #
# --------------------------------------------------------------------- #
store = StoreAI(catalogue, alpha=0.2)
customers = [CustomerAgent() for _ in range(50)]

start_date = dt.date(2025, 7, 12)
DAYS = 30

for day in range(DAYS):
    today = start_date + dt.timedelta(days=day)

    # each customer may shop once per day with some probability
    for cust in customers:
        if random.random() < 0.6:
            store.serve(today, cust)

    store.daily_tick(today)

# --------------------------------------------------------------------- #
# 3. Results                                                            #
# --------------------------------------------------------------------- #
print(f"\nFinal inventory snapshot after {DAYS} days:")
pprint.pprint(store.snapshot())

print("\nSummary:")
print(f"  Revenue         : ${store.revenue:.2f}")
print(f"  Expenses        : ${store.expenses:.2f}")
print(f"  Profit          : ${store.revenue - store.expenses:.2f}")
print(f"  Inventory Value : ${store.snapshot()['inventory_value']:.2f}")

print("\nOrders placed:")
for day, sku, qty, cost in store.orders_log:
    print(f"  {day}: ordered {qty} of {sku} costing ${cost:.2f}")
