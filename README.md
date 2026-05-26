# FastBox Delivery System

A logistics simulator for a fictional delivery company **FastBox**. Simulates one day of operations — assigning packages to agents, computing delivery distances, and generating a performance report.

---

## How to Run

```bash
python delivery_system.py <input_file.json> <output_dir> [--delays]
```

**Examples:**
```bash
python delivery_system.py base_case.json .
python delivery_system.py test_case_1.json reports/
python delivery_system.py base_case.json . --delays
```

**Arguments:**

| Argument | Description | Default |
|---|---|---|
| `input_file` | Path to the JSON input file | `base_case.json` |
| `output_dir` | Directory to save report and CSV | `.` (current dir) |
| `--delays` | Enable random delivery delays (bonus) | Off |

---

## Input Format

The script supports two JSON formats:

**Format 1 — dict style (test cases):**
```json
{
  "warehouses": { "W1": [0, 0], "W2": [50, 75] },
  "agents":     { "A1": [5, 5], "A2": [60, 60] },
  "packages": [
    { "id": "P1", "warehouse": "W1", "destination": [30, 40] }
  ]
}
```

**Format 2 — list style (base case):**
```json
{
  "warehouses": [ {"id": "W1", "location": [0, 0]} ],
  "agents":     [ {"id": "A1", "location": [5, 5]} ],
  "packages": [
    { "id": "P1", "warehouse_id": "W1", "destination": [30, 40] }
  ]
}
```

Both formats are handled automatically.

---

## Output

**`report_<input>.json`** — performance report per agent:
```json
{
  "A1": { "packages_delivered": 2, "total_distance": 121.21, "efficiency": 60.61 },
  "A2": { "packages_delivered": 2, "total_distance": 79.21,  "efficiency": 39.60 },
  "A3": { "packages_delivered": 1, "total_distance": 14.14,  "efficiency": 14.14 },
  "best_agent": "A3"
}
```

**`top_performer_<input>.csv`** — CSV export of the best agent's stats.

**Console output** — per-agent summary, ASCII map, and full route details.

---

## How It Works

1. **Parse JSON** — loads warehouses, agents, and packages; normalises both input formats
2. **Assign packages** — each package is assigned to the nearest agent by Euclidean distance from agent to the package's warehouse
3. **Simulate delivery** — agent travels: current position → warehouse (pick up) → destination (deliver), chaining trips from last drop-off position
4. **Generate report** — computes total distance and efficiency (avg distance per package) for each agent; selects best agent

---

## Bonus Features

- **Random delays** — `--delays` flag adds a random 0–30 minute delay per delivery
- **ASCII map** — visual grid showing warehouse (W), agent (A), and destination (*) positions
- **CSV export** — top performer automatically exported to CSV

---

## Assumptions

The following decisions were made for undefined/ambiguous scenarios:

- **Tie-breaking (nearest agent):** When two agents are equidistant from a warehouse, Python's `min()` picks the first one in iteration order (insertion order of the dict). This is deterministic and consistent.
- **Delivery order per agent:** Packages are delivered in the order they are listed in the input JSON. No further optimisation (e.g. TSP) is applied, as the problem does not require it.
- **Agent continuity:** After delivering a package, the agent continues from the destination of the last delivery, not from their starting position. This reflects real-world logistics behaviour.
- **Efficiency metric:** Defined as `total_distance / packages_delivered` (average distance per package). A lower score means higher efficiency. Agents with zero packages are excluded from the best-agent selection.
- **Best agent:** The agent with the lowest efficiency score (among those who delivered at least one package) is selected as the best agent.
- **Delays (bonus):** Random delays affect time only and do not alter distance calculations, since the problem defines efficiency in terms of distance.

---

## Requirements

- Python 3.7+
- No external libraries required (uses only standard library: `json`, `math`, `csv`, `sys`, `os`, `random`, `pathlib`)
