# Curry Graph Lab

An interactive, single-file lesson on how a **state-graph execution engine** works, told through the steps of making curry.

**Live page:** https://chir0rin.github.io/CurryGraphLab/

Open `index.html` (no server, no dependencies; Japanese / English toggle at the top right) and advance the graph one turn at a time:

- **Nodes** are cooking stages; **edges** are the paths between them; **state** is one shared notebook every stage reads and writes. Click a stage to see what it reads and writes.
- Watch a **conditional edge** choose a direction, a **cycle** repeat "simmer" until the potato is soft, and a **fan-out / fan-in** cook rice and pickles side by side and wait for both before plating.
- See why a **reducer** (merge rule) is needed when two stages write the same entry in the same turn.
- Every turn writes a **checkpoint**; an **interrupt** pauses before a chosen stage and waits for a human; injected failures show **retries** and a stop-with-progress-kept for manual repair.

## Python version

`python/curry_graph.py` is the same graph as a plain script, with no dependencies: superstep execution with true fan-out/fan-in, reducers driven by `Annotated[...]` type hints, a JSON checkpoint after every turn, `interrupt_before` with resume, and failure injection with retries.

```bash
python3 python/curry_graph.py                       # runs until the interrupt before add_roux
python3 python/curry_graph.py --resume --approve     # records the human note and continues
INTERRUPT_BEFORE=add_roux,taste_check python3 python/curry_graph.py          # ask at every tasting too
FAIL=cook_rice:3 RETRIES=2 python3 python/curry_graph.py --resume --approve  # fail 3 times, retry 2 → stop, keep progress
FAIL= python3 python/curry_graph.py --resume --approve                       # "repair" and continue from the checkpoint
```

## Terms (plain words first)

turn (superstep) · merge rule (reducer) · fork and repeat (conditional edge, cycle) · split and join (fan-out, fan-in) · save point (checkpoint) · ask a human (interrupt) · retry and manual repair

## License

MIT for the code and the page. The curry is yours.
