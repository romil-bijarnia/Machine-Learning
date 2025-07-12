import collections
import datetime as dt
import math
import random


class CustomerAgent:
    """Tiny learning agent representing a supermarket shopper."""

    def __init__(self, preferences: dict[str, float] | None = None):
        self.preferences = preferences or {}

    def choose_item(self, store: "StoreAI") -> tuple[str, int]:
        items = list(store.cat)
        weights = [self.preferences.get(sku, 1.0) for sku in items]
        sku = random.choices(items, weights=weights, k=1)[0]
        qty = random.randint(1, 3)
        return sku, qty

    def learn(self, sku: str, success: bool) -> None:
        mult = 1.1 if success else 0.9
        self.preferences[sku] = self.preferences.get(sku, 1.0) * mult


class StoreAI:
    """Very small-footprint inventory brain for a single supermarket."""

    def __init__(self, catalogue: dict[str, dict], alpha: float = 0.2):
        """Initialize a new ``StoreAI`` instance.

        Args:
            catalogue: mapping sku -> {case, lead, safety, cost, price}
                      case   : case‑pack size (int, must divide ordered quantity)
                      lead   : supplier lead‑time in days (int >= 0)
                      safety : units of safety stock to buffer uncertainty
                      cost   : unit cost from supplier (float)
                      price  : unit selling price (float)
            alpha: smoothing factor for exponential demand average (0 < alpha ≤ 1)
        """
        self.cat = catalogue
        self.alpha = alpha

        # keep separate cost and dynamic price tables
        self.cost = {sku: info.get("cost", 0.0) for sku, info in catalogue.items()}
        self.price = {sku: info.get("price", 0.0) for sku, info in catalogue.items()}

        # mutable state
        self.on_hand = {k: 10 for k in catalogue}       # start with 10 of each sku
        self.on_order = {k: 0 for k in catalogue}
        self.demand_hat = {k: 1.0 for k in catalogue}   # initial demand estimate (units/day)
        self.revenue = 0.0
        self.expenses = 0.0
        self.sales_log: list[tuple[dt.date, str, int]] = []

        # future deliveries pipeline: arrival_day -> list[(sku, qty)]
        self._order_pipe = collections.defaultdict(list)

        # track ordering activity
        self.orders_log: list[tuple[dt.date, str, int, float]] = []

    # --------------------------------------------------------------------- #
    #  Public API                                                           #
    # --------------------------------------------------------------------- #

    def sell(self, ts: dt.date, sku: str, qty: int = 1) -> bool:
        """Process a customer sale if stock available; update demand forecast.

        Returns:
            True if sale successful, False if out‑of‑stock.
        """
        if self.on_hand[sku] < qty:
            return False  # stock‑out

        self.on_hand[sku] -= qty
        self.sales_log.append((ts, sku, qty))
        self.revenue += self.price.get(sku, 0) * qty

        self.revenue += self.price.get(sku, 0) * qty

        self.revenue += self.cat[sku].get("price", 0) * qty


        # exponential smoothing update
        self.demand_hat[sku] = (
            self.alpha * qty + (1.0 - self.alpha) * self.demand_hat[sku]
        )
        return True

    def serve(self, ts: dt.date, customer: CustomerAgent) -> None:
        sku, qty = customer.choose_item(self)
        success = self.sell(ts, sku, qty)
        customer.learn(sku, success)

    def daily_tick(self, today: dt.date) -> None:
        """Advance simulation by one day: receive deliveries and place new orders."""
        self._receive_arrivals(today)
        self._reorder(today)
        self._adjust_prices()

    def snapshot(self) -> dict:
        """Current inventory + demand estimate (for debugging / reporting)."""
        return {
            "on_hand": self.on_hand.copy(),
            "on_order": self.on_order.copy(),
            "demand_hat": self.demand_hat.copy(),

            "price": {k: round(v, 2) for k, v in self.price.items()},
            "inventory_value": round(self._inventory_value(), 2),


            "price": {k: round(v, 2) for k, v in self.price.items()},
            "inventory_value": round(self._inventory_value(), 2),


            "revenue": round(self.revenue, 2),
            "expenses": round(self.expenses, 2),
            "profit": round(self.revenue - self.expenses, 2),
        }

    # --------------------------------------------------------------------- #
    #  Internal helpers                                                     #
    # --------------------------------------------------------------------- #

    def _receive_arrivals(self, today: dt.date) -> None:
        for sku, qty in self._order_pipe.get(today, []):
            self.on_hand[sku] += qty
            self.on_order[sku] -= qty
        self._order_pipe.pop(today, None)

    def _reorder(self, today: dt.date) -> None:
        for sku, info in self.cat.items():
            L = info["lead"]
            target_pos = self.demand_hat[sku] * L + info["safety"]
            gap = target_pos - (self.on_hand[sku] + self.on_order[sku])
            if gap <= 0:
                continue

            # round up to nearest case‑pack multiple
            case = info["case"]
            order_qty = math.ceil(gap / case) * case

            self.on_order[sku] += order_qty

            cost = order_qty * self.cost.get(sku, 0)
            self.expenses += cost


            cost = order_qty * self.cost.get(sku, 0)
            self.expenses += cost

            self.expenses += order_qty * self.cat[sku].get("cost", 0)


            arrival_day = today + dt.timedelta(days=L)
            self._order_pipe[arrival_day].append((sku, order_qty))
            self.orders_log.append((today, sku, order_qty, cost))

    def _adjust_prices(self) -> None:
        """Simple dynamic pricing based on inventory position."""
        for sku, info in self.cat.items():
            target_pos = self.demand_hat[sku] * info["lead"] + info["safety"]
            pos = self.on_hand[sku] + self.on_order[sku]
            if pos > 1.5 * target_pos:
                self.price[sku] *= 0.9
            elif pos < 0.5 * target_pos:
                self.price[sku] *= 1.1

            # keep price above cost with minimal margin
            min_price = self.cost.get(sku, 0) * 1.05
            if self.price[sku] < min_price:
                self.price[sku] = min_price

    def _inventory_value(self) -> float:
        return sum(self.on_hand[sku] * self.cost.get(sku, 0) for sku in self.cat)
