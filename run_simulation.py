"""Run a 30‑day supermarket simulation using the minimalist StoreAI."""

import datetime as dt
import random
import pprint

from store_ai import StoreAI

# --------------------------------------------------------------------- #
# 1. Static catalogue definition                                        #
# --------------------------------------------------------------------- #
catalogue = {
    "bread": {"case": 20, "lead": 2, "safety": 15},
    "milk":  {"case": 12, "lead": 1, "safety": 10},
    "eggs":  {"case": 30, "lead": 3, "safety": 25},
}

# --------------------------------------------------------------------- #
# 2. Run simulation                                                     #
# --------------------------------------------------------------------- #
store = StoreAI(catalogue, alpha=0.2)

start_date = dt.date(2025, 7, 12)
DAYS = 30

for day in range(DAYS):
    today = start_date + dt.timedelta(days=day)

    # pseudo‑random customer traffic
    for _ in range(random.randint(30, 60)):
        sku = random.choice(list(catalogue))
        store.sell(today, sku)

    store.daily_tick(today)

# --------------------------------------------------------------------- #
# 3. Results                                                            #
# --------------------------------------------------------------------- #
print(f"\nFinal inventory snapshot after {DAYS} days:")
pprint.pprint(store.snapshot())
