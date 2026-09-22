"""
カレー作りグラフ v2 — 「工学」側の 3 概念を足した版
  1. スーパーステップ実行 + 注釈駆動 Reducer(本当の並行ファンアウト/合流)
  2. チェックポイント(毎ステップ JSON 保存 → 途中再開)
  3. interrupt(指定ノードの前で止まり、人の入力を待つ)
依存なし。python3 curry_graph_v2.py [--resume] [--approve]
"""
from __future__ import annotations
import json, os, sys, typing
from operator import add
from typing import Annotated, TypedDict, Callable

# ============================================================
# STATE: 注釈が Reducer を決める(エンジンは型を読む)
# ============================================================
class CurryState(TypedDict, total=False):
    ingredients: list[str]
    missing_items: list[str]
    peeled_vegetables: list[str]
    cut_vegetables: list[str]
    cut_style: str
    meat_browned: bool
    vegetables_sauteed: bool
    water_added_ml: int
    simmer_elapsed_min: int
    potato_softness: float
    salt_g: Annotated[int, add]               # 塩は足すたびに加算(Reducer)
    roux_added: bool
    taste_result: str
    revision_count: int
    taste_history: Annotated[list[str], add]  # 追記(Reducer)
    sides_ready: Annotated[list[str], add]    # 並行ノードが同じキーへ書く → Reducer 必須
    final_dish_ready: bool
    human_note: str                           # interrupt で人が入れる


def reducers_from_annotations(cls) -> dict[str, Callable]:
    out = {}
    for name, hint in typing.get_type_hints(cls, include_extras=True).items():
        if typing.get_origin(hint) is Annotated:
            _, *meta = typing.get_args(hint)
            out[name] = meta[0]
    return out

REDUCERS = reducers_from_annotations(CurryState)

# ============================================================
# NODES(前回と同じ関数群 + 塩と付け合わせを「並行で同じキーに書く」形に)
# ============================================================
def shop_check(s):
    required = {"人参", "じゃがいも", "玉ねぎ", "豚肉", "カレールー"}
    missing = sorted(required - set(s["ingredients"]))      # 順序を決定的に
    print(f"[shop_check] 不足: {missing}"); return {"missing_items": missing}
def shop_buy_missing(s):
    print(f"[shop_buy_missing] {s['missing_items']} を購入")
    return {"ingredients": s["ingredients"] + s["missing_items"], "missing_items": []}
def peel_vegetables(s):
    peeled = [i for i in s["ingredients"] if i in ("人参", "じゃがいも")]
    print(f"[peel_vegetables] {peeled}"); return {"peeled_vegetables": peeled}
def cut_vegetables(s):
    cut = s["peeled_vegetables"] + ["玉ねぎ"]
    print(f"[cut_vegetables] {cut} を{s['cut_style']}に"); return {"cut_vegetables": cut}
def saute_meat(s):
    print("[saute_meat] 焼き色がついた"); return {"meat_browned": True}
def saute_vegetables(s):
    print("[saute_vegetables] しんなりした"); return {"vegetables_sauteed": True}
def add_water(s):
    print("[add_water] 600ml"); return {"water_added_ml": 600}
def simmer(s):
    elapsed = s.get("simmer_elapsed_min", 0) + 10
    soft = min(1.0, elapsed / 20)
    print(f"[simmer] {elapsed}分 柔らかさ {soft:.2f}"); return {"simmer_elapsed_min": elapsed, "potato_softness": soft}
def add_roux(s):
    print("[add_roux] ルー投入"); return {"roux_added": True}
def taste_check(s):
    count = s.get("revision_count", 0) + 1
    result = "良好" if s.get("salt_g", 0) >= 2 else "薄い"     # 回数ではなく塩分で判定
    print(f"[taste_check] {count}回目 塩{s.get('salt_g',0)}g -> {result}")
    return {"taste_result": result, "revision_count": count, "taste_history": [result]}
def add_salt(s):
    print("[add_salt] +1g"); return {"salt_g": 1}                 # Reducer(add)で加算される
def cook_rice(s):
    print("[cook_rice] 炊けた"); return {"sides_ready": ["ご飯"]}
def prepare_pickles(s):
    print("[prepare_pickles] 用意した"); return {"sides_ready": ["福神漬け"]}
def plate(s):
    print(f"[plate] 付け合わせ {s['sides_ready']} / メモ: {s.get('human_note','')}"); return {"final_dish_ready": True}

NODES = {f.__name__: f for f in [shop_check, shop_buy_missing, peel_vegetables, cut_vegetables, saute_meat,
                                 saute_vegetables, add_water, simmer, add_roux, taste_check, add_salt,
                                 cook_rice, prepare_pickles, plate]}

# ============================================================
# EDGES: 次ノードは「リスト」(複数 = ファンアウト)。合流は次ノードの依存で待つ
# ============================================================
def route_after_shop_check(s): return ["shop_buy_missing"] if s["missing_items"] else ["peel_vegetables"]
def route_after_simmer(s):     return ["add_roux"] if s["potato_softness"] >= 1.0 else ["simmer"]
def route_after_taste(s):      return ["add_salt"] if s["taste_result"] == "薄い" else ["cook_rice", "prepare_pickles"]  # ← ファンアウト

EDGES: dict[str, Callable | list[str]] = {
    "shop_check": route_after_shop_check, "shop_buy_missing": ["peel_vegetables"], "peel_vegetables": ["cut_vegetables"],
    "cut_vegetables": ["saute_meat"], "saute_meat": ["saute_vegetables"], "saute_vegetables": ["add_water"],
    "add_water": ["simmer"], "simmer": route_after_simmer, "add_roux": ["taste_check"], "taste_check": route_after_taste,
    "add_salt": ["taste_check"], "cook_rice": ["plate"], "prepare_pickles": ["plate"], "plate": [],
}
JOIN = {"plate": {"cook_rice", "prepare_pickles"}}   # plate は両方が終わるまで待つ(ファンイン)
START = "shop_check"
INTERRUPT_BEFORE = {"add_roux"}                     # ここで止まって人に聞く
CHECKPOINT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curry_checkpoint.json")

# ============================================================
# ENGINE: スーパーステップ + Reducer + チェックポイント + interrupt
# ============================================================
def apply(state: dict, updates: list[dict]) -> dict:
    new = dict(state)
    for upd in updates:                       # 同じステップの更新を順に畳み込む
        for k, v in upd.items():
            new[k] = REDUCERS[k](new.get(k, type(v)()), v) if k in REDUCERS else v
    return new

def save(step, frontier, done, state):
    json.dump({"step": step, "frontier": sorted(frontier), "done": sorted(done), "state": state},
              open(CHECKPOINT, "w"), ensure_ascii=False, indent=1)

def run(initial: dict, resume=False, approve=False, max_steps=40):
    if resume and os.path.exists(CHECKPOINT):
        cp = json.load(open(CHECKPOINT)); step, frontier, done, state = cp["step"], set(cp["frontier"]), set(cp["done"]), cp["state"]
        print(f"=== チェックポイントから再開 (step {step}, 次: {sorted(frontier)}) ===")
    else:
        step, frontier, done, state = 0, {START}, set(), dict(initial)

    while frontier and step < max_steps:
        # interrupt: 停止対象が次にあり、承認が無ければ保存して止まる
        stop = frontier & INTERRUPT_BEFORE
        if stop and not approve:
            save(step, frontier, done, state)
            print(f"\n⏸ interrupt: {sorted(stop)} の前で停止。味見の前にルーの種類を決めて。\n   再開: python3 {os.path.basename(__file__)} --resume --approve")
            return state
        approve = False                       # 承認は 1 回分だけ有効
        step += 1
        ready = {n for n in frontier if JOIN.get(n, set()) <= done}   # ファンイン: 依存が揃ったものだけ
        print(f"\n--- SUPERSTEP {step}: {sorted(ready)} ---")
        updates = [NODES[n](state) for n in sorted(ready)]           # 本来は並列。ここは順に呼ぶが結果は同時に合流
        state = apply(state, updates)
        done |= ready
        nxt = set()
        for n in ready:
            e = EDGES[n]; nxt |= set(e(state) if callable(e) else e)
        frontier = (frontier - ready) | nxt
        save(step, frontier, done, state)
    print("\n=== 最終 State ===")
    for k, v in state.items(): print(f"  {k}: {v}")
    return state

if __name__ == "__main__":
    args = set(sys.argv[1:])
    init = {"ingredients": ["人参", "じゃがいも", "豚肉"], "cut_style": "一口大", "salt_g": 0,
            "revision_count": 0, "taste_history": [], "sides_ready": []}
    if "--approve" in args:                    # 人の入力を state に載せて再開(interrupt の返答)
        cp = json.load(open(CHECKPOINT)); cp["state"]["human_note"] = "ルーは中辛で"; json.dump(cp, open(CHECKPOINT, "w"), ensure_ascii=False)
    run(init, resume="--resume" in args, approve="--approve" in args)
