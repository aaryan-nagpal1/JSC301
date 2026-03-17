import random
from copy import deepcopy
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="Blind Box Value Maximizer",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] {display:none;}
    .stApp {
        background: #f8fafc;
        color: #0f172a;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1220px;
    }
    h1, h2, h3 { color: #0f172a; }
    p, li { color: #475569; }
    .hero-title {
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        line-height: 1.05;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .hero-sub {
        text-align: center;
        max-width: 860px;
        margin: 0 auto 1.25rem auto;
        color: #475569;
        font-size: 1.08rem;
    }
    .eyebrow {
        font-size: 0.9rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        color: #2563eb;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }
    .big-title {
        font-size: 3rem;
        font-weight: 900;
        line-height: 1.05;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    .muted {
        color: #475569;
        font-size: 1rem;
    }
    .chip {
        display:inline-block;
        background:#eef2ff;
        color:#4338ca;
        border:1px solid #c7d2fe;
        border-radius:999px;
        padding:6px 12px;
        font-size:0.8rem;
        font-weight:700;
        margin-bottom:10px;
    }
    .metric-card {
        background: white;
        border: 1px solid #dbeafe;
        border-radius: 22px;
        padding: 18px 20px;
        box-shadow: 0 8px 26px rgba(15,23,42,0.04);
        min-height: 120px;
    }
    .metric-label {
        font-size: 0.82rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #64748b;
        margin-bottom: 12px;
        font-weight: 700;
    }
    .metric-value {
        font-size: 2.25rem;
        font-weight: 900;
        color: #0f172a;
    }
    .pill-good, .pill-bad, .pill-neutral {
        display:inline-block;
        padding:8px 14px;
        border-radius:999px;
        font-weight:800;
        font-size:0.95rem;
    }
    .pill-good { background:#dcfce7; color:#166534; }
    .pill-bad { background:#fee2e2; color:#991b1b; }
    .pill-neutral { background:#e0f2fe; color:#075985; }
    .math-step {
        background:#f8fafc;
        border:1px solid #e2e8f0;
        border-radius:18px;
        padding:16px;
        margin-bottom:12px;
        color:#334155;
    }
    .result-row {
        background: white;
        border:1px solid #e2e8f0;
        border-radius: 20px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 6px 20px rgba(15,23,42,0.04);
    }
    .result-head {
        font-size: 0.78rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .result-main {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
    }
    .stButton > button {
        width: 100%;
        border-radius: 16px;
        border: 1px solid #2563eb;
        background: #2563eb;
        color: white !important;
        font-weight: 800;
        padding: 0.85rem 1rem;
        box-shadow: 0 8px 22px rgba(37,99,235,0.18);
    }
    .stButton > button:hover {
        background: #1d4ed8;
        border-color: #1d4ed8;
        color: white !important;
    }
    .stButton > button[kind="secondary"] {
        background: white;
        color: #0f172a !important;
        border: 1px solid #cbd5e1;
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #f8fafc;
        color: #0f172a !important;
        border-color: #94a3b8;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 24px;
        padding: 18px;
        box-shadow: 0 10px 28px rgba(15,23,42,0.05);
    }
    .stImage img {
        border-radius: 18px;
    }
    .stAlert {
        display:none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

ASSETS = Path(__file__).parent / "assets"


def currency(x: float) -> str:
    return f"${x:,.2f}"


def ev_of(payouts):
    return sum(p["value"] * p["probability"] for p in payouts)


def best_outcome(payouts):
    return max(payouts, key=lambda x: x["value"])


def fairness_label(ev: float, cost: float) -> str:
    diff = ev - cost
    if diff > 2:
        return "Arbitrage Opportunity"
    if abs(diff) <= 2:
        return "Approximately Fair"
    return "Unfavourable Purchase"


def fairness_class(ev: float, cost: float) -> str:
    diff = ev - cost
    if diff > 2:
        return "pill-good"
    if abs(diff) <= 2:
        return "pill-neutral"
    return "pill-bad"


def random_int(low: int, high: int) -> int:
    low = int(round(low))
    high = int(round(high))
    if low > high:
        low, high = high, low
    return random.randint(low, high)


def weighted_random_choice(payouts):
    r = random.random()
    cumulative = 0.0
    for p in payouts:
        cumulative += p["probability"]
        if r <= cumulative:
            return p
    return payouts[-1]


def load_img(filename: str):
    path = ASSETS / filename
    return str(path) if path.exists() else None


def show_image(filename: str, caption: str):
    path = load_img(filename)
    if path:
        st.image(path, caption=caption, use_container_width=True)
    else:
        st.info(f"Add assets/{filename}")


def metric_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_pill(text: str, cls: str):
    st.markdown(f'<div class="{cls}">{text}</div>', unsafe_allow_html=True)


def scenario_math(scenario):
    ev = ev_of(scenario["payouts"])
    best = best_outcome(scenario["payouts"])
    blind_box_net = ev - scenario["blind_box_cost"]
    direct_net = best["value"] - scenario["direct_buy_price"]
    optimal = "Blind Box" if blind_box_net > direct_net else "Direct Buy"
    return {
        "ev": ev,
        "best": best,
        "blind_box_net": blind_box_net,
        "direct_net": direct_net,
        "optimal": optimal,
        "fairness": fairness_label(ev, scenario["blind_box_cost"]),
    }


def multi_math(scenario):
    single_ev = ev_of(scenario["payouts"])
    best = best_outcome(scenario["payouts"])
    option_rows = []
    for k in [1, 2, 3, 4]:
        total_ev = k * single_ev
        total_cost = k * scenario["single_box_cost"]
        net = total_ev - total_cost
        option_rows.append({
            "label": f"{k} Blind Box" + ("es" if k > 1 else ""),
            "k": k,
            "ev": total_ev,
            "cost": total_cost,
            "net": net,
        })
    direct_value = best["value"]
    direct_net = direct_value - scenario["direct_buy_price"]
    option_rows.append({
        "label": "Direct Buy",
        "k": 0,
        "ev": direct_value,
        "cost": scenario["direct_buy_price"],
        "net": direct_net,
    })
    optimal_row = max(option_rows, key=lambda x: x["net"])
    return {
        "single_ev": single_ev,
        "best": best,
        "options": option_rows,
        "optimal": optimal_row["label"],
    }


def build_randomized_single(template: dict):
    scenario = deepcopy(template)
    payouts = scenario["payouts"]
    ev = ev_of(payouts)
    best = best_outcome(payouts)
    if scenario["target_optimal"] == "Blind Box":
        blind_net = random_int(5, 10)
        direct_net = random_int(-2, blind_net - 2)
    else:
        direct_net = random_int(4, 9)
        blind_net = random_int(-4, direct_net - 2)
    scenario["blind_box_cost"] = max(1, random_int(ev - blind_net - 0.49, ev - blind_net + 0.49))
    scenario["direct_buy_price"] = max(1, random_int(best["value"] - direct_net - 0.49, best["value"] - direct_net + 0.49))
    return scenario


def build_randomized_multi(template: dict):
    scenario = deepcopy(template)
    single_ev = ev_of(scenario["payouts"])
    best_val = best_outcome(scenario["payouts"])["value"]
    if scenario["target_optimal"] == "Direct Buy":
        box_margin = random_int(-3, 1)
        direct_margin = random_int(12, 22)
    else:
        box_margin = random_int(4, 8)
        direct_margin = random_int(-3, 2)
    scenario["single_box_cost"] = max(1, random_int(single_ev - box_margin - 0.49, single_ev - box_margin + 0.49))
    scenario["direct_buy_price"] = max(1, random_int(best_val - direct_margin - 0.49, best_val - direct_margin + 0.49))
    return scenario


def generate_single_scenarios():
    return [build_randomized_single(t) for t in SINGLE_TEMPLATES]


def generate_multi_scenarios():
    return [build_randomized_multi(t) for t in MULTI_TEMPLATES]


def init_state():
    defaults = {
        "screen": "intro",
        "mode": None,
        "scenario_index": 0,
        "history": [],
        "selected_choice": None,
        "resolved": None,
        "single_scenarios": [],
        "multi_scenarios": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_all():
    for k in ["screen", "mode", "scenario_index", "history", "selected_choice", "resolved", "single_scenarios", "multi_scenarios"]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


def start_mode(mode: str):
    st.session_state.mode = mode
    st.session_state.scenario_index = 0
    st.session_state.history = []
    st.session_state.selected_choice = None
    st.session_state.resolved = None
    st.session_state.single_scenarios = generate_single_scenarios()
    st.session_state.multi_scenarios = generate_multi_scenarios()
    st.session_state.screen = "choice"


def current_scenario():
    if st.session_state.mode == "demo":
        return DEMO_SCENARIO
    if st.session_state.mode == "game":
        return st.session_state.single_scenarios[st.session_state.scenario_index]
    if st.session_state.mode == "multi":
        return st.session_state.multi_scenarios[st.session_state.scenario_index]
    return None


def resolve_single(choice: str, scenario: dict):
    math = scenario_math(scenario)
    if choice == "Blind Box":
        outcome = weighted_random_choice(scenario["payouts"])
        cost = scenario["blind_box_cost"]
    else:
        outcome = math["best"]
        cost = scenario["direct_buy_price"]
    net = outcome["value"] - cost
    st.session_state.selected_choice = choice
    st.session_state.resolved = {"math": math, "outcome": outcome, "cost": cost, "net": net}
    if st.session_state.mode == "game":
        st.session_state.history.append({
            "scenario": scenario["title"],
            "choice": choice,
            "optimal": math["optimal"],
            "correct": choice == math["optimal"],
            "net": net,
            "outcome": outcome["label"],
        })
    st.session_state.screen = "math_single"


def resolve_multi(choice: str, scenario: dict):
    math = multi_math(scenario)
    chosen = next(o for o in math["options"] if o["label"] == choice)
    if chosen["label"] == "Direct Buy":
        outcome = {"label": math["best"]["label"], "value": math["best"]["value"], "image": math["best"]["image"]}
    else:
        draws = [weighted_random_choice(scenario["payouts"]) for _ in range(chosen["k"])]
        outcome = {
            "label": " + ".join(d["label"] for d in draws),
            "value": sum(d["value"] for d in draws),
            "image": draws[0]["image"],
        }
    cost = chosen["cost"]
    net = outcome["value"] - cost
    st.session_state.selected_choice = choice
    st.session_state.resolved = {"math": math, "outcome": outcome, "cost": cost, "net": net, "chosen": chosen}
    if st.session_state.mode == "multi":
        st.session_state.history.append({
            "scenario": scenario["title"],
            "choice": choice,
            "optimal": math["optimal"],
            "correct": choice == math["optimal"],
            "net": net,
            "outcome": outcome["label"],
        })
    st.session_state.screen = "math_multi"


def next_step():
    if st.session_state.mode == "demo":
        reset_all()
        return
    total = len(st.session_state.multi_scenarios) if st.session_state.mode == "multi" else len(st.session_state.single_scenarios)
    if st.session_state.scenario_index < total - 1:
        st.session_state.scenario_index += 1
        st.session_state.selected_choice = None
        st.session_state.resolved = None
        st.session_state.screen = "choice"
    else:
        st.session_state.screen = "summary"


def score_summary():
    correct = sum(1 for h in st.session_state.history if h["correct"])
    net = sum(h["net"] for h in st.session_state.history)
    return correct, net


DEMO_SCENARIO = {
    "title": "Demo Game",
    "subtitle": "Warm-up round: use intuition first, then check the math.",
    "blind_box_cost": 20,
    "direct_buy_price": 34,
    "blind_box_image": "blindbox.jpg",
    "direct_image": "direct_buy.jpg",
    "payouts": [
        {"label": "Labubu Common A", "value": 10, "probability": 0.35, "image": "common_a.jpg"},
        {"label": "Labubu Common B", "value": 14, "probability": 0.30, "image": "common_b.jpg"},
        {"label": "Labubu Rare", "value": 36, "probability": 0.20, "image": "rare.jpg"},
        {"label": "Labubu Secret", "value": 75, "probability": 0.15, "image": "secret.jpg"},
    ],
}

SINGLE_TEMPLATES = [
    {
        "title": "Starter Shelf",
        "subtitle": "One rare item makes the gamble tempting.",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "target_optimal": "Blind Box",
        "payouts": [
            {"label": "Labubu Common A", "value": 12, "probability": 0.35, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 15, "probability": 0.30, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 45, "probability": 0.20, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 80, "probability": 0.15, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Arbitrage Alert",
        "subtitle": "The blind box is surprisingly underpriced.",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "target_optimal": "Blind Box",
        "payouts": [
            {"label": "Labubu Common A", "value": 14, "probability": 0.20, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 18, "probability": 0.25, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 40, "probability": 0.35, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 70, "probability": 0.20, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Collector Rush",
        "subtitle": "High hype, but most outcomes are weaker than they seem.",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "target_optimal": "Direct Buy",
        "payouts": [
            {"label": "Labubu Common A", "value": 8, "probability": 0.32, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 11, "probability": 0.33, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 30, "probability": 0.25, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 90, "probability": 0.10, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Balanced Box",
        "subtitle": "Close enough that intuition can easily fail.",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "target_optimal": "Direct Buy",
        "payouts": [
            {"label": "Labubu Common A", "value": 10, "probability": 0.25, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 18, "probability": 0.35, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 28, "probability": 0.25, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 50, "probability": 0.15, "image": "secret.jpg"},
        ],
    },
]

MULTI_TEMPLATES = [
    {
        "title": "Quantity Challenge A",
        "subtitle": "Choose 1, 2, 3, or 4 blind boxes, or take the direct buy instead.",
        "target_optimal": "Direct Buy",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": DEMO_SCENARIO["payouts"],
    },
    {
        "title": "Quantity Challenge B",
        "subtitle": "The blind-box side is stronger here on expected value. Which quantity wins?",
        "target_optimal": "4 Blind Boxes",
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": DEMO_SCENARIO["payouts"],
    },
]

init_state()
if not st.session_state.single_scenarios:
    st.session_state.single_scenarios = generate_single_scenarios()
if not st.session_state.multi_scenarios:
    st.session_state.multi_scenarios = generate_multi_scenarios()
scenario = current_scenario()

if st.session_state.screen == "intro":
    st.markdown('<div class="hero-title">Blind Box Value Maximizer</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Use Labubu-style blind boxes to learn expected value, fairness, and decision-making under uncertainty. Start with a demo, the full single-box game, or the quantity-choice challenge.</div>', unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a:
        metric_card("Core Idea", "Expected Value")
    with b:
        metric_card("Compare", "Risk vs Certainty")
    with c:
        metric_card("Question", "Fair or Not?")

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        with st.container(border=True):
            st.markdown('<div class="chip">Option 1</div>', unsafe_allow_html=True)
            st.markdown("### Demo Game")
            st.write("Demo round. Make a choice, then see the math reveal on the next screen.")
            show_image("blindbox.jpg", "Demo preview")
            if st.button("Start Demo Game", key="start_demo"):
                start_mode("demo")
                st.rerun()
    with c2:
        with st.container(border=True):
            st.markdown('<div class="chip">Option 2</div>', unsafe_allow_html=True)
            st.markdown("### Full Game")
            st.write("Play four randomized single-box rounds with a balanced split of optimal answers.")
            show_image("direct_buy.jpg", "Full game preview")
            if st.button("Start Full Game", key="start_full"):
                start_mode("game")
                st.rerun()
    with c3:
        with st.container(border=True):
            st.markdown('<div class="chip">Option 3</div>', unsafe_allow_html=True)
            st.markdown("### Quantity Challenge")
            st.write("Choose between 1, 2, 3, or 4 blind boxes and compare them against direct buy.")
            show_image("rare.jpg", "Quantity challenge preview")
            if st.button("Start Quantity Challenge", key="start_multi"):
                start_mode("multi")
                st.rerun()

elif st.session_state.screen == "choice":
    top1, top2 = st.columns([1, 1])
    with top1:
        if st.button("← Main Menu", key="menu_choice", type="secondary", use_container_width=False):
            reset_all()
            st.rerun()
    with top2:
        label = "Demo Round" if st.session_state.mode == "demo" else (
            f"Round {st.session_state.scenario_index + 1} of {len(st.session_state.single_scenarios)}" if st.session_state.mode == "game" else f"Round {st.session_state.scenario_index + 1} of {len(st.session_state.multi_scenarios)}"
        )
        st.markdown(f'<div style="text-align:right; color:#64748b; padding-top:8px;">{label}</div>', unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Choose First</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-title">{scenario["title"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="muted">{scenario["subtitle"]}</div>', unsafe_allow_html=True)
    st.write("")

    if st.session_state.mode == "multi":
        mm = multi_math(scenario)
        a, b = st.columns(2)
        with a:
            metric_card("Per Box Cost", currency(scenario["single_box_cost"]))
        with b:
            metric_card("Direct Buy", currency(scenario["direct_buy_price"]))

        st.write("")
        st.markdown("### Possible Box Outcomes")
        st.markdown("<div class='muted'>Each blind box is an independent draw from the following 4 possible Labubu figures.</div>", unsafe_allow_html=True)
        legend_cols = st.columns(4, gap="small")
        for col, item in zip(legend_cols, scenario["payouts"]):
            with col:
                with st.container(border=True):
                    show_image(item["image"], item["label"])
                    st.markdown(f"**{item['label']}**")
                    st.write(f"Value: **{currency(item['value'])}**")
                    st.write(f"Chance: **{(item['probability'] * 100):.0f}%**")

        st.write("")
        cols = st.columns(5, gap="small")
        option_labels = ["1 Blind Box", "2 Blind Boxes", "3 Blind Boxes", "4 Blind Boxes", "Direct Buy"]
        for col, option_label in zip(cols, option_labels):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {option_label}")
                    if option_label == "Direct Buy":
                        show_image(scenario["direct_image"], option_label)
                        st.write("Direct buy guarantees the highest-value figure immediately.")
                        st.write(f"Guaranteed item: **{mm['best']['label']}**")
                        st.write(f"Price: **{currency(scenario['direct_buy_price'])}**")
                        if st.button("Choose", key=f"choose_{option_label}"):
                            resolve_multi(option_label, scenario)
                            st.rerun()
                    else:
                        k = int(option_label.split()[0])
                        show_image(scenario["blind_box_image"], option_label)
                        st.write(f"{k} independent draws")
                        st.write("Each box can contain any one of the 4 figures shown above.")
                        st.write(f"Total cost: **{currency(k * scenario['single_box_cost'])}**")
                        if st.button("Choose", key=f"choose_{option_label}"):
                            resolve_multi(option_label, scenario)
                            st.rerun()
    else:
        sm = scenario_math(scenario)
        a, b = st.columns(2)
        with a:
            metric_card("Blind Box Cost", currency(scenario["blind_box_cost"]))
        with b:
            metric_card("Direct Buy", currency(scenario["direct_buy_price"]))

        left, right = st.columns(2, gap="large")
        with left:
            with st.container(border=True):
                st.markdown("### Blind Box")
                show_image(scenario["blind_box_image"], "Blind Box")
                st.write(f"Pay **{currency(scenario['blind_box_cost'])}** and receive one figure at random.")
                for item in scenario["payouts"]:
                    st.markdown(f"- **{item['label']}** · {currency(item['value'])} · {(item['probability'] * 100):.0f}%")
                if st.button("Choose Blind Box", key="choose_single_box"):
                    resolve_single("Blind Box", scenario)
                    st.rerun()
        with right:
            with st.container(border=True):
                st.markdown("### Direct Buy")
                show_image(scenario["direct_image"], "Direct Buy")
                st.write(f"Pay **{currency(scenario['direct_buy_price'])}** and lock in the top-value figure immediately.")
                st.write(f"Guaranteed item: **{sm['best']['label']}**")
                st.write(f"Market value: **{currency(sm['best']['value'])}**")
                if st.button("Choose Direct Buy", key="choose_direct"):
                    resolve_single("Direct Buy", scenario)
                    st.rerun()

elif st.session_state.screen == "math_single":
    resolved = st.session_state.resolved
    math = resolved["math"]
    outcome = resolved["outcome"]
    choice = st.session_state.selected_choice
    was_correct = choice == math["optimal"]
    correct, total_net = score_summary()

    top1, top2 = st.columns([1, 1])
    with top1:
        if st.button("← Main Menu", key="menu_math_single", type="secondary", use_container_width=False):
            reset_all()
            st.rerun()
    with top2:
        if st.session_state.mode == "game":
            st.markdown(f'<div style="text-align:right; color:#64748b; padding-top:8px;">Score: {correct} correct · {currency(total_net)} total net</div>', unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Math Reveal</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-title">{"You were right" if was_correct else "Not quite"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="muted">You chose <b>{choice}</b>. The optimal long-run decision was <b>{math["optimal"]}</b>.</div>', unsafe_allow_html=True)
    result_pill("Correct Decision" if was_correct else "Suboptimal Decision", "pill-good" if was_correct else "pill-bad")
    st.write("")

    a, b, c, d = st.columns(4)
    with a:
        metric_card("Expected Value", currency(math["ev"]))
    with b:
        metric_card("Blind Box Net", currency(math["blind_box_net"]))
    with c:
        metric_card("Direct Buy Net", currency(math["direct_net"]))
    with d:
        metric_card("Your Result", currency(resolved["net"]))

    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Why?")
            eq_terms = " + ".join([f"{p['value']}×{p['probability']}" for p in scenario["payouts"]])
            st.markdown(f'<div class="math-step"><b>Step 1:</b> E(X) = {eq_terms} = <b>{currency(math["ev"])}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="math-step"><b>Step 2:</b> {currency(math["ev"])} - {currency(scenario["blind_box_cost"])} = <b>{currency(math["blind_box_net"])}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="math-step"><b>Step 3:</b> {currency(math["best"]["value"])} - {currency(scenario["direct_buy_price"])} = <b>{currency(math["direct_net"])}</b></div>', unsafe_allow_html=True)
            cmp_symbol = ">" if math["blind_box_net"] > math["direct_net"] else "<="
            st.markdown(f'<div class="math-step"><b>Step 4:</b> Since <b>{currency(math["blind_box_net"])}</b> {cmp_symbol} <b>{currency(math["direct_net"])}</b>, the better long-run decision is <b>{math["optimal"]}</b>.</div>', unsafe_allow_html=True)
            result_pill(math["fairness"], fairness_class(math["ev"], scenario["blind_box_cost"]))
    with right:
        with st.container(border=True):
            st.markdown("### Your Outcome")
            show_image(outcome["image"], outcome["label"])
            metric_card("Market Value", currency(outcome["value"]))
            metric_card("Cost Paid", currency(resolved["cost"]))
            metric_card("Net Result", currency(resolved["net"]))
        with st.container(border=True):
            st.markdown("### Possible Outcomes")
            for item in scenario["payouts"]:
                with st.expander(f"{item['label']} · {currency(item['value'])} · {(item['probability'] * 100):.0f}%"):
                    show_image(item["image"], item["label"])
        if st.button("Next", key="next_single"):
            next_step()
            st.rerun()

elif st.session_state.screen == "math_multi":
    resolved = st.session_state.resolved
    math = resolved["math"]
    outcome = resolved["outcome"]
    choice = st.session_state.selected_choice
    was_correct = choice == math["optimal"]
    correct, total_net = score_summary()

    top1, top2 = st.columns([1, 1])
    with top1:
        if st.button("← Main Menu", key="menu_math_multi", type="secondary", use_container_width=False):
            reset_all()
            st.rerun()
    with top2:
        st.markdown(f'<div style="text-align:right; color:#64748b; padding-top:8px;">Score: {correct} correct · {currency(total_net)} total net</div>', unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Math Reveal</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="big-title">{"You were right" if was_correct else "Not quite"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="muted">You chose <b>{choice}</b>. The optimal long-run decision was <b>{math["optimal"]}</b>.</div>', unsafe_allow_html=True)
    result_pill("Correct Decision" if was_correct else "Suboptimal Decision", "pill-good" if was_correct else "pill-bad")
    st.write("")

    a, b, c, d = st.columns(4)
    chosen = resolved["chosen"]
    with a:
        metric_card("EV of 1 Box", currency(math["single_ev"]))
    with b:
        metric_card("Chosen Option EV", currency(chosen["ev"]))
    with c:
        metric_card("Direct Buy Net", currency(next(o["net"] for o in math["options"] if o["label"] == "Direct Buy")))
    with d:
        metric_card("Your Result", currency(resolved["net"]))

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("### Quantity Comparison")
            for row in math["options"]:
                pill = "pill-good" if row["label"] == math["optimal"] else "pill-neutral"
                st.markdown(
                    f"<div class='result-row'><div class='result-head'>{row['label']}</div><div class='result-main'>Expected net: {currency(row['net'])}</div><div class='muted'>Expected value {currency(row['ev'])} · Cost {currency(row['cost'])}</div></div>",
                    unsafe_allow_html=True,
                )
                if row["label"] == math["optimal"]:
                    result_pill("Best expected choice", pill)
        with st.container(border=True):
            st.markdown("### Why?")
            st.markdown(f'<div class="math-step"><b>Step 1:</b> Compute the expected value of 1 blind box: <b>{currency(math["single_ev"])}</b>.</div>', unsafe_allow_html=True)
            st.markdown('<div class="math-step"><b>Step 2:</b> Because the boxes are independent, the expected value of k boxes is k × EV(1 box).</div>', unsafe_allow_html=True)
            st.markdown('<div class="math-step"><b>Step 3:</b> Compare the expected net of 1, 2, 3, and 4 blind boxes against the guaranteed net of direct buy.</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="math-step"><b>Step 4:</b> The highest expected net here is <b>{math["optimal"]}</b>.</div>', unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            st.markdown("### Your Realized Outcome")
            show_image(outcome["image"], outcome["label"])
            metric_card("Realized Value", currency(outcome["value"]))
            metric_card("Cost Paid", currency(resolved["cost"]))
            metric_card("Realized Net", currency(resolved["net"]))
        if st.button("Next", key="next_multi"):
            next_step()
            st.rerun()

elif st.session_state.screen == "summary":
    correct, total_net = score_summary()
    total_rounds = len(st.session_state.multi_scenarios) if st.session_state.mode == "multi" else len(st.session_state.single_scenarios)

    st.markdown('<div class="hero-title">Final Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">You finished the game. Review your performance, then play again.</div>', unsafe_allow_html=True)

    a, b, c = st.columns(3)
    with a:
        metric_card("Correct Choices", f"{correct}/{total_rounds}")
    with b:
        metric_card("Total Net", currency(total_net))
    with c:
        metric_card("Main Goal", "Beat intuition with math")

    st.write("")
    st.markdown("### Round-by-Round Results")
    for item in st.session_state.history:
        cols = st.columns([1.3, 1.15, 1.15, 0.8, 1.4])
        with cols[0]:
            st.markdown(f"<div class='result-row'><div class='result-head'>Scenario</div><div class='result-main'>{item['scenario']}</div></div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<div class='result-row'><div class='result-head'>Your Choice</div><div class='result-main'>{item['choice']}</div></div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<div class='result-row'><div class='result-head'>Optimal</div><div class='result-main'>{item['optimal']}</div></div>", unsafe_allow_html=True)
        with cols[3]:
            pill = 'pill-good' if item['correct'] else 'pill-bad'
            text = 'Correct' if item['correct'] else 'Missed'
            st.markdown(f"<div class='result-row'><div class='result-head'>Result</div><div style='margin-top:8px;'><span class='{pill}'>{text}</span></div></div>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"<div class='result-row'><div class='result-head'>Net / Outcome</div><div class='result-main'>{currency(item['net'])}</div><div class='muted'>{item['outcome']}</div></div>", unsafe_allow_html=True)

    tips = st.columns(3)
    with tips[0]:
        with st.container(border=True):
            st.markdown("### Expected Value")
            st.write("A higher average long-run return matters more than one lucky draw.")
    with tips[1]:
        with st.container(border=True):
            st.markdown("### Risk vs Certainty")
            st.write("Sometimes the guaranteed purchase is better. Sometimes the gamble is underpriced.")
    with tips[2]:
        with st.container(border=True):
            st.markdown("### Quantity Matters")
            st.write("With multiple boxes, expected value scales linearly, but realized outcomes can still vary a lot.")

    if st.button("Play Again", key="play_again"):
        reset_all()
        st.rerun()