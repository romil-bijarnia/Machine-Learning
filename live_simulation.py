"""Run an open-ended supermarket simulation with a simple live display."""

import datetime as dt
import random
import time
from store_ai import StoreAI, CustomerAgent

catalogue = {
    "bread": {"case": 20, "lead": 2, "safety": 15, "cost": 1.2, "price": 2.5},
    "milk":  {"case": 12, "lead": 1, "safety": 10, "cost": 0.6, "price": 1.5},
    "eggs":  {"case": 30, "lead": 3, "safety": 25, "cost": 2.0, "price": 3.5},
}

store = StoreAI(catalogue)
customers = [CustomerAgent() for _ in range(50)]

today = dt.date(2025, 7, 12)

day = 0
try:
    while True:
        for cust in customers:
            if random.random() < 0.6:
                store.serve(today, cust)
        store.daily_tick(today)
        snap = store.snapshot()
        print(
            f"Day {day:4d} | Profit ${snap['profit']:.2f} | On hand {snap['on_hand']}",
            end="\r",
            flush=True,
        )
        day += 1
        today += dt.timedelta(days=1)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nSimulation terminated by user.")
    print(store.snapshot())
