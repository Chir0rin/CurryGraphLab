from typing import TypedDict, Callable, Annotated
from operator import add

class CurryState(TypedDict):
    ingredients: list[str]; missing_items: list[str]
    peeled_vegetables: list[str]; cut_vegetables: list[str]; cut_style: str
    meat_browned: bool; vegetables_sauteed: bool
    water_added_ml: int; simmer_elapsed_min: int; potato_softness: float
    roux_added: bool; taste_result: str; revision_count: int
    taste_history: Annotated[list[str], add]
    rice_cooked: bool; pickles_ready: bool; final_dish_ready: bool

def shop_check(state):
    required = {"人参", "じゃがいも", "玉ねぎ", "豚肉", "カレールー"}
    missing = list(required - set(state["ingredients"]))
    print(f"[shop_check] 手持ち: {state['ingredients']} / 不足: {missing}")
    return {"missing_items": missing}
def shop_buy_missing(state):
    bought = state["ingredients"] + state["missing_items"]
    print(f"[shop_buy_missing] {state['missing_items']} を購入")
    return {"ingredients": bought, "missing_items": []}
def peel_vegetables(state):
    targets = [i for i in state["ingredients"] if i in ["人参", "じゃがいも"]]
    peeled = []
    for v in targets:
        peeled.append(v); print(f"[peel_vegetables]   {v} の皮を剥いた")
    return {"peeled_vegetables": peeled}
def cut_vegetables(state):
    style = state["cut_style"]; cut = []
    for v in state["peeled_vegetables"] + ["玉ねぎ"]:
        cut.append(v); print(f"[cut_vegetables]   {v} を{style}にカット")
    return {"cut_vegetables": cut}
def saute_meat(state):
    print("[saute_meat] 豚肉を炒めている... 焼き色がついた"); return {"meat_browned": True}
def saute_vegetables(state):
    print(f"[saute_vegetables] {state['cut_vegetables']} を炒めている... しんなりした"); return {"vegetables_sauteed": True}
def add_water(state):
    print("[add_water] 水600mlを投入"); return {"water_added_ml": 600}
def simmer(state):
    elapsed = state.get("simmer_elapsed_min", 0) + 10
    softness = min(1.0, elapsed / 20)
    print(f"[simmer] {elapsed}分経過。じゃがいもの柔らかさ: {softness:.2f}")
    return {"simmer_elapsed_min": elapsed, "potato_softness": softness}
def add_roux(state):
    print("[add_roux] ルーを溶かし入れた"); return {"roux_added": True}
def taste_check(state):
    count = state.get("revision_count", 0) + 1
    result = "薄い" if count == 1 else "良好"
    print(f"[taste_check] {count}回目の味見 -> 判定: {result}")
    return {"taste_result": result, "revision_count": count, "taste_history": [result]}
def add_salt(state):
    print("[add_salt] 塩を少量追加"); return {}
def cook_rice(state):
    print("[cook_rice] ご飯が炊き上がった（煮込みと並行して進行）"); return {"rice_cooked": True}
def prepare_pickles(state):
    print("[prepare_pickles] 福神漬けを用意した（煮込みと並行して進行）"); return {"pickles_ready": True}
def plate(state):
    print(f"[plate] 盛り付け完了。ご飯:{state['rice_cooked']} 漬物:{state['pickles_ready']}"); return {"final_dish_ready": True}

def route_after_shop_check(state): return "shop_buy_missing" if state["missing_items"] else "peel_vegetables"
def route_after_simmer(state): return "add_roux" if state["potato_softness"] >= 1.0 else "simmer"
def route_after_taste(state): return "add_salt" if state["taste_result"] == "薄い" else "cook_rice"

NODES = {n: globals()[n] for n in ["shop_check","shop_buy_missing","peel_vegetables","cut_vegetables","saute_meat","saute_vegetables","add_water","simmer","add_roux","taste_check","add_salt","cook_rice","prepare_pickles","plate"]}
FIXED_EDGES = {"shop_buy_missing":"peel_vegetables","peel_vegetables":"cut_vegetables","cut_vegetables":"saute_meat","saute_meat":"saute_vegetables","saute_vegetables":"add_water","add_water":"simmer","add_roux":"taste_check","add_salt":"taste_check","cook_rice":"prepare_pickles","prepare_pickles":"plate"}
CONDITIONAL_EDGES = {"shop_check": route_after_shop_check, "simmer": route_after_simmer, "taste_check": route_after_taste}
START_NODE, END_NODE = "shop_check", "plate"

def run_graph(initial_state, max_steps=40):
    state = dict(initial_state); current = START_NODE; step = 0
    while step < max_steps:
        step += 1
        print(f"\n--- STEP {step}: [{current}] ---")
        updates = NODES[current](state)
        for k, v in updates.items():
            if k == "taste_history": state[k] = state.get(k, []) + v
            else: state[k] = v
        if current == END_NODE: break
        current = CONDITIONAL_EDGES[current](state) if current in CONDITIONAL_EDGES else FIXED_EDGES[current]
    print("\n=== 最終State ===")
    for k, v in state.items(): print(f"  {k}: {v}")
    return state

if __name__ == "__main__":
    run_graph({"ingredients": ["人参","じゃがいも","豚肉"], "missing_items": [], "peeled_vegetables": [], "cut_vegetables": [], "cut_style": "一口大",
               "meat_browned": False, "vegetables_sauteed": False, "water_added_ml": 0, "simmer_elapsed_min": 0, "potato_softness": 0.0,
               "roux_added": False, "taste_result": "", "revision_count": 0, "taste_history": [], "rice_cooked": False, "pickles_ready": False, "final_dish_ready": False})
