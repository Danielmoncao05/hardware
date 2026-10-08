"""Measures standard filtered inventory-list latency (task 6.2; target p95 <= 2 s at 10,000 records).

Prerequisite: a test deployment with >= 10,000 equipment rows (xano function setup/seed_perf_data).
Nominal load = CONCURRENCY parallel users issuing paginated, filtered list requests.

    HHM_TEST_ADMIN_EMAIL=... HHM_TEST_ADMIN_PASSWORD=... python tests/perf/inventory_list_p95.py [requests] [concurrency]

Prints the setup and percentiles so the result can be recorded; exits 1 when p95 > 2 s.
"""

import asyncio
import os
import random
import statistics
import sys
import time

import httpx

BASE = os.environ.get("XANO_BASE_URL", "https://x8ki-letl-twmt.n7.xano.io").rstrip("/")
AUTH = os.environ.get("XANO_AUTH_GROUP", "9o8FUxuc")
INVENTORY = os.environ.get("XANO_INVENTORY_GROUP", "hhm149197-inventory")
TARGET_P95 = 2.0


async def main(requests: int, concurrency: int) -> int:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{BASE}/api:{AUTH}/auth/login",
            json={"email": os.environ["HHM_TEST_ADMIN_EMAIL"], "password": os.environ["HHM_TEST_ADMIN_PASSWORD"]},
        )
        r.raise_for_status()
        headers = {"Authorization": f"Bearer {r.json()['authToken']}"}
        url = f"{BASE}/api:{INVENTORY}/equipamentos"

        first = (await client.get(url, headers=headers, params={"per_page": 1})).json()
        locs = (await client.get(f"{BASE}/api:{INVENTORY}/localizacoes", headers=headers)).json()
        cats = (await client.get(f"{BASE}/api:{INVENTORY}/categorias", headers=headers)).json()

        # Standard list views: unfiltered first page, and by status, location, category, text search
        def params() -> dict:
            p = {"page": random.randint(1, 20), "per_page": 25}
            kind = random.choice(["none", "status", "loc", "cat", "q"])
            if kind == "status":
                p["status"] = random.choice(["operational", "under_maintenance", "out_of_service"])
            elif kind == "loc" and locs:
                p["localizacao_id"] = random.choice(locs)["id"]
            elif kind == "cat" and cats:
                p["categoria_id"] = random.choice(cats)["id"]
            elif kind == "q":
                p["q"] = f"PERF-{random.randint(1, 9999)}"
            return p

        latencies: list[float] = []
        errors = 0
        sem = asyncio.Semaphore(concurrency)

        async def one():
            nonlocal errors
            async with sem:
                t0 = time.perf_counter()
                resp = await client.get(url, headers=headers, params=params())
                latencies.append(time.perf_counter() - t0)
                if resp.status_code != 200:
                    errors += 1

        await asyncio.gather(*(one() for _ in range(requests)))

    latencies.sort()
    q = statistics.quantiles(latencies, n=100)
    print(f"base url        : {BASE}")
    print(f"active records  : {first.get('itemsTotal')}")
    print(f"requests        : {requests} ({errors} errors), concurrency {concurrency}")
    print(f"p50 / p95 / p99 : {q[49]:.3f}s / {q[94]:.3f}s / {q[98]:.3f}s   max {latencies[-1]:.3f}s")
    ok = q[94] <= TARGET_P95 and errors == 0
    print("RESULT          :", "PASS" if ok else "FAIL", f"(target p95 <= {TARGET_P95}s)")
    return 0 if ok else 1


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    c = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    sys.exit(asyncio.run(main(n, c)))
