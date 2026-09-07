from concurrent.futures import ThreadPoolExecutor

import pytest

from core.request_budget import RequestBudget, RequestBudgetExceeded


def test_budget_blocks_the_request_after_the_limit() -> None:
    budget = RequestBudget(limit=2)

    assert budget.reserve() == 1
    assert budget.reserve() == 2
    with pytest.raises(RequestBudgetExceeded):
        budget.reserve()

    assert budget.count == 2
    assert budget.remaining == 0


def test_budget_is_atomic_across_scanners() -> None:
    budget = RequestBudget(limit=60)

    def attempt_reservation(_: int) -> bool:
        try:
            budget.reserve()
        except RequestBudgetExceeded:
            return False
        return True

    with ThreadPoolExecutor(max_workers=8) as executor:
        reservations = list(executor.map(attempt_reservation, range(100)))

    assert sum(reservations) == 60
    assert budget.count == 60

