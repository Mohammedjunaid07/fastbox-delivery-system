import json
import math
import csv
import sys
import os
import random
from pathlib import Path


def euclidean(p1: list, p2: list) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def load_data(path: str) -> dict:
    with open(path, "r") as f:
        raw = json.load(f)

    wh = raw["warehouses"]
    if isinstance(wh, list):
        warehouses = {w["id"]: w["location"] for w in wh}
    else:
        warehouses = wh

    ag = raw["agents"]
    if isinstance(ag, list):
        agents = {a["id"]: a["location"] for a in ag}
    else:
        agents = ag

    packages = []
    for p in raw["packages"]:
        wid = p.get("warehouse") or p.get("warehouse_id")
        packages.append({
            "id": p["id"],
            "warehouse": wid,
            "destination": p["destination"]
        })

    return {"warehouses": warehouses, "agents": agents, "packages": packages}


def assign_packages(agents: dict, warehouses: dict, packages: list) -> dict:
    assignment = {aid: [] for aid in agents}

    for pkg in packages:
        wh_loc = warehouses[pkg["warehouse"]]
        nearest = min(agents, key=lambda aid: euclidean(agents[aid], wh_loc))
        assignment[nearest].append(pkg)

    return assignment


def simulate(agents: dict, warehouses: dict, assignment: dict,
             enable_delays: bool = False) -> dict:
    results = {}

    for agent_id, pkgs in assignment.items():
        pos = list(agents[agent_id])
        total_dist = 0.0
        delivered = []
        route = [f"Start {pos}"]

        for pkg in pkgs:
            wh_loc = warehouses[pkg["warehouse"]]
            dest = pkg["destination"]

            d1 = euclidean(pos, wh_loc)
            total_dist += d1
            pos = list(wh_loc)
            route.append(f"→ {pkg['warehouse']} {pos} (+{d1:.2f})")

            if enable_delays:
                delay = random.randint(0, 30)

            d2 = euclidean(pos, dest)
            total_dist += d2
            pos = list(dest)
            route.append(f"→ {pkg['id']} dest {pos} (+{d2:.2f})")

            delivered.append(pkg["id"])

        n = len(delivered)
        efficiency = round(total_dist / n, 2) if n > 0 else 0.0

        results[agent_id] = {
            "packages_delivered": n,
            "total_distance": round(total_dist, 2),
            "efficiency": efficiency,
            "route": route
        }

    return results


def build_report(sim_results: dict) -> dict:
    report = {}
    best_agent = None
    best_eff = float("inf")

    for aid, stats in sim_results.items():
        report[aid] = {
            "packages_delivered": stats["packages_delivered"],
            "total_distance": stats["total_distance"],
            "efficiency": stats["efficiency"]
        }
        if stats["packages_delivered"] > 0 and stats["efficiency"] < best_eff:
            best_eff = stats["efficiency"]
            best_agent = aid

    report["best_agent"] = best_agent
    return report


def ascii_map(agents: dict, warehouses: dict, packages: list,
              assignment: dict, width: int = 60, height: int = 30) -> str:
    grid = [["." for _ in range(width)] for _ in range(height)]

    all_x = ([v[0] for v in agents.values()] +
              [v[0] for v in warehouses.values()] +
              [p["destination"][0] for p in packages])
    all_y = ([v[1] for v in agents.values()] +
              [v[1] for v in warehouses.values()] +
              [p["destination"][1] for p in packages])

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)

    def to_grid(x, y):
        gx = int((x - min_x) / max(max_x - min_x, 1) * (width - 1))
        gy = int((y - min_y) / max(max_y - min_y, 1) * (height - 1))
        return gx, height - 1 - gy

    for wid, loc in warehouses.items():
        gx, gy = to_grid(*loc)
        grid[gy][gx] = "W"

    for aid, loc in agents.items():
        gx, gy = to_grid(*loc)
        grid[gy][gx] = "A"

    for pkg in packages:
        gx, gy = to_grid(*pkg["destination"])
        if grid[gy][gx] == ".":
            grid[gy][gx] = "*"

    lines = ["=" * width, "ASCII MAP  W=Warehouse  A=Agent  *=Destination", "=" * width]
    lines += ["".join(row) for row in grid]
    lines.append("=" * width)
    return "\n".join(lines)


def export_top_performer(report: dict, out_path: str):
    best = report["best_agent"]
    if not best:
        return
    stats = report[best]
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["agent", "packages_delivered",
                                               "total_distance", "efficiency"])
        writer.writeheader()
        writer.writerow({
            "agent": best,
            "packages_delivered": stats["packages_delivered"],
            "total_distance": stats["total_distance"],
            "efficiency": stats["efficiency"]
        })
    print(f"[CSV] Top performer exported → {out_path}")


def run(input_path: str, output_dir: str = ".", enable_delays: bool = False,
        show_ascii: bool = True):
    print(f"\n{'='*60}")
    print(f" FastBox Delivery Simulation")
    print(f" Input: {input_path}")
    print(f"{'='*60}")

    data = load_data(input_path)
    agents = data["agents"]
    warehouses = data["warehouses"]
    packages = data["packages"]

    print(f" Warehouses : {len(warehouses)}")
    print(f" Agents     : {len(agents)}")
    print(f" Packages   : {len(packages)}")

    assignment = assign_packages(agents, warehouses, packages)
    sim_results = simulate(agents, warehouses, assignment, enable_delays)
    report = build_report(sim_results)

    stem = Path(input_path).stem
    report_path = os.path.join(output_dir, f"report_{stem}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[REPORT] Saved → {report_path}")

    print("\n── Per-Agent Summary ──────────────────────────────────")
    for aid in sorted(k for k in report if k != "best_agent"):
        s = report[aid]
        print(f"  {aid}: {s['packages_delivered']} pkgs  "
              f"dist={s['total_distance']:.2f}  "
              f"efficiency={s['efficiency']:.2f}")
    print(f"\n  ★ Best Agent: {report['best_agent']}")

    if show_ascii:
        print("\n" + ascii_map(agents, warehouses, packages, assignment))

    csv_path = os.path.join(output_dir, f"top_performer_{stem}.csv")
    export_top_performer(report, csv_path)

    print("\n── Route Details ──────────────────────────────────────")
    for aid, stats in sim_results.items():
        print(f"\n  {aid}:")
        for step in stats["route"]:
            print(f"    {step}")

    return report


if __name__ == "__main__":
    try:
        get_ipython
        _in_jupyter = True
    except NameError:
        _in_jupyter = False

    if _in_jupyter:
        input_file    = "base_case.json"
        output_dir    = "."
        enable_delays = False
    else:
        input_file    = sys.argv[1] if len(sys.argv) > 1 else "base_case.json"
        output_dir    = sys.argv[2] if len(sys.argv) > 2 else "."
        enable_delays = "--delays" in sys.argv

    run(input_file, output_dir, enable_delays=enable_delays, show_ascii=True)
