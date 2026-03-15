import random
from pathlib import Path

import streamlit as st

# ---------- Page config ----------
st.set_page_config(
    page_title="Blind Box Value Maximizer",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #1e1b4b 0%, #0f172a 45%, #020617 100%);
        color: white;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    .hero {
        background: linear-gradient(135deg, rgba(99,102,241,0.22), rgba(16,185,129,0.16));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 28px;
        padding: 28px;
        margin-bottom: 18px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.20);
    }
    .glass {
        background: rgba(15,23,42,0.70);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 24px;
        padding: 20px;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }
    .stat {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 16px 18px;
        margin-bottom: 10px;
    }
    .stat-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #cbd5e1;
        margin-bottom: 6px;
    }
    .stat-value {
        font-size: 1.55rem;
        font-weight: 800;
        color: white;
    }
    .choice-card {
        background: rgba(15,23,42,0.82);
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 24px;
        padding: 18px;
        min-height: 100%;
    }
    .pill-good, .pill-bad, .pill-neutral {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 999px;
        font-weight: 700;
        font-size: 0.92rem;
        margin-top: 6px;
    }
    .pill-good { background: rgba(16,185,129,0.16); color: #6ee7b7; }
    .pill-bad { background: rgba(244,63,94,0.16); color: #fda4af; }
    .pill-neutral { background: rgba(56,189,248,0.16); color: #7dd3fc; }
    .step {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .small-muted {
        color: #cbd5e1;
        font-size: 0.95rem;
    }
    .center-title {
        text-align: center;
        font-size: 2.9rem;
        font-weight: 900;
        line-height: 1.05;
        margin-bottom: 0.5rem;
        color: white;
    }
    .center-sub {
        text-align: center;
        font-size: 1.08rem;
        color: #dbeafe;
        max-width: 860px;
        margin: 0 auto 1.5rem auto;
    }
    .result-box {
        background: linear-gradient(135deg, rgba(15,23,42,0.92), rgba(30,41,59,0.88));
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 24px;
        padding: 22px;
    }
    .summary-box {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 20px;
        padding: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Helpers ----------
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


def image_or_placeholder(filename: str, caption: str, use_container_width=True, height=None):
    path = load_img(filename)
    if path:
        st.image(path, caption=caption, use_container_width=use_container_width)
    else:
        st.markdown(
            f"""
            <div class="summary-box" style="min-height:{height or 220}px; display:flex; align-items:center; justify-content:center; text-align:center;">
                <div>
                    <div style="font-size:2rem;">🖼️</div>
                    <div style="font-weight:700; color:white; margin-top:6px;">{caption}</div>
                    <div class="small-muted" style="margin-top:6px;">Add assets/{filename}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def stat_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="stat">
            <div class="stat-label">{label}</div>
            <div class="stat-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def init_state():
    defaults = {
        "screen": "intro",
        "mode": None,
        "scenario_index": 0,
        "history": [],
        "selected_choice": None,
        "resolved_outcome": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_all():
    for k in ["screen", "mode", "scenario_index", "history", "selected_choice", "resolved_outcome"]:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


def start_mode(mode: str):
    st.session_state.mode = mode
    st.session_state.scenario_index = 0
    st.session_state.history = []
    st.session_state.selected_choice = None
    st.session_state.resolved_outcome = None
    st.session_state.screen = "choice"


def resolve_choice(choice: str, scenario: dict):
    math = scenario_math(scenario)
    if choice == "Blind Box":
        outcome = weighted_random_choice(scenario["payouts"])
        cost = scenario["blind_box_cost"]
    else:
        outcome = math["best"]
        cost = scenario["direct_buy_price"]

    net = outcome["value"] - cost

    st.session_state.selected_choice = choice
    st.session_state.resolved_outcome = {
        "outcome": outcome,
        "cost": cost,
        "net": net,
        "math": math,
    }

    if st.session_state.mode == "game":
        st.session_state.history.append(
            {
                "scenario_title": scenario["title"],
                "choice": choice,
                "optimal": math["optimal"],
                "correct": choice == math["optimal"],
                "net": net,
                "outcome": outcome["label"],
            }
        )

    st.session_state.screen = "math"


def next_step():
    if st.session_state.mode == "demo":
        reset_all()
        st.rerun()

    if st.session_state.scenario_index < len(MAIN_SCENARIOS) - 1:
        st.session_state.scenario_index += 1
        st.session_state.selected_choice = None
        st.session_state.resolved_outcome = None
        st.session_state.screen = "choice"
    else:
        st.session_state.screen = "summary"
    st.rerun()


def running_score():
    hist = st.session_state.history
    correct = sum(1 for h in hist if h["correct"])
    net = sum(h["net"] for h in hist)
    return correct, net


# ---------- Assets ----------
ASSETS = Path(__file__).parent / "assets"

# Expected image files:
# blindbox.jpg, direct_buy.jpg, common_a.jpg, common_b.jpg, rare.jpg, secret.jpg

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

MAIN_SCENARIOS = [
    {
        "title": "Starter Shelf",
        "subtitle": "One rare item makes the gamble tempting.",
        "blind_box_cost": 20,
        "direct_buy_price": 32,
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": [
            {"label": "Labubu Common A", "value": 12, "probability": 0.35, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 15, "probability": 0.30, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 45, "probability": 0.20, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 80, "probability": 0.15, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Collector Rush",
        "subtitle": "High hype, but most outcomes are weaker than they seem.",
        "blind_box_cost": 22,
        "direct_buy_price": 40,
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": [
            {"label": "Labubu Common A", "value": 8, "probability": 0.32, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 11, "probability": 0.33, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 30, "probability": 0.25, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 90, "probability": 0.10, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Balanced Box",
        "subtitle": "This one is close enough that intuition can easily fail.",
        "blind_box_cost": 18,
        "direct_buy_price": 28,
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": [
            {"label": "Labubu Common A", "value": 10, "probability": 0.25, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 18, "probability": 0.35, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 28, "probability": 0.25, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 50, "probability": 0.15, "image": "secret.jpg"},
        ],
    },
    {
        "title": "Arbitrage Alert",
        "subtitle": "The blind box is surprisingly underpriced.",
        "blind_box_cost": 16,
        "direct_buy_price": 34,
        "blind_box_image": "blindbox.jpg",
        "direct_image": "direct_buy.jpg",
        "payouts": [
            {"label": "Labubu Common A", "value": 14, "probability": 0.20, "image": "common_a.jpg"},
            {"label": "Labubu Common B", "value": 18, "probability": 0.25, "image": "common_b.jpg"},
            {"label": "Labubu Rare", "value": 40, "probability": 0.35, "image": "rare.jpg"},
            {"label": "Labubu Secret", "value": 70, "probability": 0.20, "image": "secret.jpg"},
        ],
    },
]


# ---------- UI Screens ----------
init_state()

if st.session_state.mode == "demo":
    current_scenario = DEMO_SCENARIO
elif st.session_state.mode == "game":
    current_scenario = MAIN_SCENARIOS[st.session_state.scenario_index]
else:
    current_scenario = None


if st.session_state.screen == "intro":
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown('<div class="center-title">Blind Box Value Maximizer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="center-sub">Use Labubu-style blind boxes to learn expected value, fairness, arbitrage, and decision-making under uncertainty. Start with a demo or jump into the full game.</div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        stat_card("Core idea", "Expected Value")
    with c2:
        stat_card("Compare", "Risk vs Certainty")
    with c3:
        stat_card("Question", "Fair or Not?")
    st.markdown('</div>', unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("🎁 Demo Game")
        st.write("Play one polished example first. Make a choice, then go to a separate math reveal screen that explains whether you were right or wrong.")
        image_or_placeholder("blindbox.jpg", "Demo preview", height=280)
        if st.button("Start Demo Game", use_container_width=True, type="primary"):
            start_mode("demo")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("🏆 Blind Box Value Maximization Game")
        st.write("Play all rounds, compare intuition against expected value, and track your score and total net performance.")
        image_or_placeholder("direct_buy.jpg", "Full game preview", height=280)
        if st.button("Start Full Game", use_container_width=True):
            start_mode("game")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.screen == "choice":
    math = scenario_math(current_scenario)

    top_left, top_right = st.columns([1, 1])
    with top_left:
        if st.button("← Main Menu"):
            reset_all()
            st.rerun()
    with top_right:
        if st.session_state.mode == "demo":
            st.markdown('<div style="text-align:right; padding-top:8px; color:#dbeafe;">Demo Round</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div style="text-align:right; padding-top:8px; color:#dbeafe;">Round {st.session_state.scenario_index + 1} of {len(MAIN_SCENARIOS)}</div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.85rem; text-transform:uppercase; letter-spacing:0.2em; color:#93c5fd;'>Choose First</div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:2.6rem; font-weight:900; color:white; line-height:1.05; margin-top:4px;'>{current_scenario['title']}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='small-muted' style='margin-top:10px;'>{current_scenario['subtitle']}</div>", unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        stat_card("Blind Box Cost", currency(current_scenario["blind_box_cost"]))
    with b:
        stat_card("Direct Buy", currency(current_scenario["direct_buy_price"]))
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="choice-card">', unsafe_allow_html=True)
        image_or_placeholder(current_scenario["blind_box_image"], "Blind Box")
        st.markdown("### Blind Box")
        st.write(f"Pay **{currency(current_scenario['blind_box_cost'])}** and receive one of the following figures at random. No expected value is shown yet — trust your intuition first.")
        for item in current_scenario["payouts"]:
            st.markdown(
                f"- **{item['label']}** · {currency(item['value'])} · {(item['probability'] * 100):.0f}%"
            )
        if st.button("Choose Blind Box", use_container_width=True, type="primary"):
            resolve_choice("Blind Box", current_scenario)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="choice-card">', unsafe_allow_html=True)
        image_or_placeholder(current_scenario["direct_image"], "Direct Buy")
        st.markdown("### Direct Buy")
        st.write(f"Pay **{currency(current_scenario['direct_buy_price'])}** and lock in the highest-value figure immediately. The math comparison is revealed only after you choose.")
        best = math["best"]
        st.markdown(
            f"**Guaranteed item:** {best['label']}  \\\n**Market value:** {currency(best['value'])}"
        )
        if st.button("Choose Direct Buy", use_container_width=True):
            resolve_choice("Direct Buy", current_scenario)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.screen == "math":
    result = st.session_state.resolved_outcome
    math = result["math"]
    outcome = result["outcome"]
    choice = st.session_state.selected_choice
    was_correct = choice == math["optimal"]
    correct_count, net_total = running_score()

    left_top, right_top = st.columns([1, 1])
    with left_top:
        if st.button("← Main Menu"):
            reset_all()
            st.rerun()
    with right_top:
        if st.session_state.mode == "game":
            st.markdown(
                f"<div style='text-align:right; padding-top:8px; color:#dbeafe;'>Score: {correct_count} correct · {currency(net_total)} total net</div>",
                unsafe_allow_html=True,
            )

    main_left, main_right = st.columns([1.25, 0.75], gap="large")

    with main_left:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown(
            f"<div style='font-size:0.82rem; text-transform:uppercase; letter-spacing:0.2em; color:#cbd5e1;'>Math Reveal</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='font-size:2.4rem; font-weight:900; color:white; margin-top:6px;'>{'You were right' if was_correct else 'Not quite'}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div class='small-muted' style='margin-top:10px;'>You chose <b>{choice}</b>. The optimal long-run decision was <b>{math['optimal']}</b>.</div>",
            unsafe_allow_html=True,
        )
        pill_cls = "pill-good" if was_correct else "pill-bad"
        pill_text = "Correct Decision" if was_correct else "Suboptimal Decision"
        st.markdown(f"<div class='{pill_cls}'>{pill_text}</div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a, b, c, d = st.columns(4)
        with a:
            stat_card("Expected Value", currency(math["ev"]))
        with b:
            stat_card("Blind Box Net", currency(math["blind_box_net"]))
        with c:
            stat_card("Direct Buy Net", currency(math["direct_net"]))
        with d:
            stat_card("Your Result", currency(result["net"]))

        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("Why?")
        eq_terms = " + ".join([f"{p['value']}×{p['probability']}" for p in current_scenario["payouts"]])
        st.markdown(
            f"""
            <div class="step">
                <b>Step 1:</b> Compute the blind box expected value.<br><br>
                E(X) = {eq_terms} = <b>{currency(math['ev'])}</b>
            </div>
            <div class="step">
                <b>Step 2:</b> Subtract the blind box cost.<br><br>
                {currency(math['ev'])} - {currency(current_scenario['blind_box_cost'])} = <b>{currency(math['blind_box_net'])}</b>
            </div>
            <div class="step">
                <b>Step 3:</b> Compute the guaranteed direct-buy net.<br><br>
                {currency(math['best']['value'])} - {currency(current_scenario['direct_buy_price'])} = <b>{currency(math['direct_net'])}</b>
            </div>
            <div class="step">
                <b>Step 4:</b> Compare the two net values.<br><br>
                Since <b>{currency(math['blind_box_net'])}</b> {'>' if math['blind_box_net'] > math['direct_net'] else '<='} <b>{currency(math['direct_net'])}</b>, the better long-run decision is <b>{math['optimal']}</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with main_right:
        st.markdown('<div class="glass">', unsafe_allow_html=True)
        image_or_placeholder(outcome["image"], outcome["label"])
        st.subheader(f"You got: {outcome['label']}")
        stat_card("Market Value", currency(outcome["value"]))
        stat_card("Cost Paid", currency(result["cost"]))
        stat_card("Net Result", currency(result["net"]))
        st.markdown(
            f"<div class='{fairness_class(math['ev'], current_scenario['blind_box_cost'])}'>{math['fairness']}</div>",
            unsafe_allow_html=True,
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="glass">', unsafe_allow_html=True)
        st.subheader("Possible Blind Box Outcomes")
        for item in current_scenario["payouts"]:
            exp = st.expander(f"{item['label']} · {currency(item['value'])} · {(item['probability'] * 100):.0f}%")
            with exp:
                image_or_placeholder(item["image"], item["label"])
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("Next", use_container_width=True, type="primary"):
            next_step()

elif st.session_state.screen == "summary":
    correct_count, net_total = running_score()

    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("<div class='center-title'>Final Results</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='center-sub'>You finished the full Blind Box Value Maximization Game. Review your performance, then play again or change the images and values for your presentation.</div>",
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    with a:
        stat_card("Correct Choices", f"{correct_count}/{len(MAIN_SCENARIOS)}")
    with b:
        stat_card("Total Net", currency(net_total))
    with c:
        stat_card("Main Goal", "Beat intuition with math")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass">', unsafe_allow_html=True)
    st.subheader("Round-by-Round Results")
    st.dataframe(st.session_state.history, use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="summary-box"><h4>Expected Value</h4><div class="small-muted">A higher average long-run return matters more than one lucky outcome.</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="summary-box"><h4>Risk vs Certainty</h4><div class="small-muted">Sometimes the guaranteed purchase is better. Sometimes the gamble is underpriced.</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="summary-box"><h4>Fairness & Arbitrage</h4><div class="small-muted">A game is favourable when expected value clearly beats the price paid.</div></div>', unsafe_allow_html=True)

    if st.button("Play Again", use_container_width=True, type="primary"):
        reset_all()
        st.rerun()