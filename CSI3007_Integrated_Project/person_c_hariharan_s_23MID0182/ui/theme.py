"""Neumorphism design system for Person C's dashboard.

Soft-UI surfaces on a single light-grey canvas: raised cards with paired
light/dark shadows, inset input wells, pressed button states, and an amber
accent for emphasis. Applied by injecting CSS into Streamlit; business logic
is untouched. Component states (hover, focus, active) stay clearly visible
so controls remain recognisable.
"""

from __future__ import annotations

import streamlit as st

DESIGN_SYSTEM = "Neumorphism"

_NEU_CSS = """
<style>
/* ---------- Neumorphism · Person C (Hariharan S · 23MID0182) ---------- */
:root {
  --neu-bg: #e4ebf5;
  --neu-surface: #e4ebf5;
  --neu-text: #334155;
  --neu-muted: #64748b;
  --neu-accent: #d97706;
  --neu-dark: #c2ccda;
  --neu-light: #ffffff;
  --neu-raised: -9px -9px 18px var(--neu-light), 9px 9px 18px var(--neu-dark);
  --neu-inset: inset -5px -5px 10px var(--neu-light),
               inset 5px 5px 10px var(--neu-dark);
}

/* Single-tone canvas — essential for the soft-UI illusion */
html, body, .stApp {
  background: var(--neu-bg) !important;
  color: var(--neu-text);
}

header[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar: continuous with the canvas, subtle right relief */
section[data-testid="stSidebar"] > div {
  background: var(--neu-bg) !important;
  border-right: 2px solid rgba(194, 204, 218, 0.55);
  box-shadow: 6px 0 14px rgba(194, 204, 218, 0.35);
}

/* Main panels: raised soft surfaces */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--neu-surface);
  border: 1px solid rgba(255, 255, 255, 0.55);
  border-radius: 22px;
  box-shadow: var(--neu-raised);
}

/* Metrics: raised tiles with inset value wells */
[data-testid="stMetric"] {
  background: var(--neu-surface);
  border-radius: 20px;
  padding: 18px 20px;
  box-shadow: var(--neu-raised);
  border: 1px solid rgba(255, 255, 255, 0.55);
}
[data-testid="stMetricValue"] { color: var(--neu-accent); font-weight: 700; }
[data-testid="stMetricLabel"] p { color: var(--neu-muted) !important; }

/* Buttons: raised, pressable (inset when active) */
.stButton > button, [data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
  background: var(--neu-surface) !important;
  color: #475569 !important;
  font-weight: 600 !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  border-radius: 16px !important;
  box-shadow: var(--neu-raised) !important;
  transition: box-shadow .12s ease, transform .12s ease, color .12s ease;
}
.stButton > button:hover { color: var(--neu-accent) !important; transform: translateY(-1px); }
.stButton > button:active, .stButton > button:focus {
  box-shadow: var(--neu-inset) !important;
  transform: translateY(0);
}
.stButton > button[kind="primary"], [data-testid="baseButton-primary"] {
  color: var(--neu-accent) !important;
  border-color: rgba(217, 119, 6, 0.25) !important;
}
.stDownloadButton > button {
  background: var(--neu-surface) !important;
  border-radius: 16px !important;
  box-shadow: var(--neu-raised) !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  color: #475569 !important;
}

/* Inputs: inset wells — obviously fillable */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTimeInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  border-radius: 16px !important;
  border: 1px solid rgba(194, 204, 218, 0.7) !important;
  background: var(--neu-surface) !important;
  box-shadow: var(--neu-inset) !important;
  color: var(--neu-text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--neu-accent) !important;
}

/* Dataframes: raised frames */
[data-testid="stDataFrame"] {
  border-radius: 18px !important;
  overflow: hidden;
  box-shadow: var(--neu-raised);
  border: 1px solid rgba(255, 255, 255, 0.55);
}

/* Tabs: inset active chip */
[data-testid="stTabs"] [data-baseweb="tab"] {
  border-radius: 14px;
  background: var(--neu-surface);
  padding: 8px 16px;
}
[data-testid="stTabs"] [aria-selected="true"] {
  box-shadow: var(--neu-inset);
  color: var(--neu-accent);
}

/* Alerts / expanders */
[data-testid="stAlert"] {
  border-radius: 18px !important;
  border: 1px solid rgba(194, 204, 218, 0.6) !important;
  box-shadow: var(--neu-inset);
}
[data-testid="stExpander"] {
  border-radius: 20px !important;
  border: 1px solid rgba(255, 255, 255, 0.55) !important;
  background: var(--neu-surface) !important;
  box-shadow: var(--neu-raised);
}

/* Sliders: inset track */
[data-testid="stSlider"] [data-baseweb="slider"] > div {
  background: var(--neu-inset);
  border-radius: 8px;
}

a { color: var(--neu-accent); }
:focus-visible { outline: 3px solid var(--neu-accent); outline-offset: 2px; }
</style>
"""


def apply_theme() -> None:
    """Inject the Neumorphism stylesheet (call once after set_page_config)."""
    st.markdown(_NEU_CSS, unsafe_allow_html=True)
