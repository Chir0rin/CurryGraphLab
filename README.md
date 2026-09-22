# Curry Graph Lab

An interactive, single-file lesson on how a **state-graph execution engine** works, told through the steps of making curry.

**Live page:** https://chir0rin.github.io/CurryGraphLab/

Open `index.html` (no server, no dependencies; Japanese / English toggle at the top right) and advance the graph one turn at a time:

- **Nodes** are cooking stages; **edges** are the paths between them; **state** is one shared notebook every stage reads and writes. Click a stage to see what it reads and writes.
- Watch a **conditional edge** choose a direction, a **cycle** repeat "simmer" until the potato is soft, and a **fan-out / fan-in** cook rice and pickles side by side and wait for both before plating.
- See why a **reducer** (merge rule) is needed when two stages write the same entry in the same turn.
- Every turn writes a **checkpoint**; an **interrupt** pauses before a chosen stage and waits for a human; injected failures show **retries** and a stop-with-progress-kept for manual repair.

## Python versions

`python/` holds the same graph as plain scripts, in three steps:

| File | Adds |
|---|---|
| `curry_graph_v1.py` | the original: state, nodes, fixed and conditional edges, a cycle, a hand-coded reducer, a serial executor |
| `curry_graph_v2.py` | superstep execution with true fan-out/fan-in, reducers driven by `Annotated[...]` type hints, checkpoint to JSON, `interrupt_before` with `--resume --approve` |
| `curry_graph_v3.py` | v2 + failure injection and retries via environment variables (`FAIL=cook_rice:3 RETRIES=2`), stop with the frontier kept, resume after repair |

```bash
python3 python/curry_graph_v2.py            # stops before add_roux
python3 python/curry_graph_v2.py --resume --approve
FAIL=cook_rice:3 RETRIES=2 python3 python/curry_graph_v3.py --resume --approve
```

## Terms (plain words first)

turn (superstep) · merge rule (reducer) · fork and repeat (conditional edge, cycle) · split and join (fan-out, fan-in) · save point (checkpoint) · ask a human (interrupt) · retry and manual repair

## License

MIT for the code and the page. The curry is yours.
