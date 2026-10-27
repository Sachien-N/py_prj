"""Claymorphism design system for Person A's dashboard.

Soft, rounded, tactile surfaces: pastel palette, layered "clay" shadows
(light top-left, tinted bottom-right), generous border radius and clear
hierarchy. Applied by injecting CSS into Streamlit; no business logic is
affected. Accessible contrast ratios are preserved for body text.
"""

from __future__ import annotations

import streamlit as st

DESIGN_SYSTEM = "Claymorphism"

_CLAY_CSS = """
<style>
/* ---------- Claymorphism · Person A (Sachien N · 23MID0255) ---------- */
:root {
  --clay-bg-1: #eef1fb;
  --clay-bg-2: #fdf1f7;
  --clay-surface: #ffffff;
  --clay-text: #3b3b58;
  --clay-muted: #6b7191;
  --clay-accent: #7c6ff0;
  --clay-accent-soft: #eceafd;
  --clay-teal: #0f766e;
  --clay-radius: 26px;
  --clay-shadow: -10px -10px 22px rgba(255, 255, 255, 0.9),
                  12px 14px 30px rgba(124, 111, 240, 0.16);
}

/* App background: soft pastel gradient */
html, body, .stApp {
  background: linear-gradient(135deg, var(--clay-bg-1) 0%, var(--clay-bg-2) 100%) !important;
  color: var(--clay-text);
}

/* Hide the default header bar background */
header[data-testid="stHeader"] {
  background: transparent !important;
}

/* Sidebar: soft clay panel */
section[data-testid="stSidebar"] > div {
  background: linear-gradient(160deg, #ffffff 0%, #f3f0ff 100%) !important;
  border-right: 1px solid rgba(124, 111, 240, 0.12);
}

/* Cards: main blocks get the clay surface treatment */
[data-testid="stMain"] .stMarkdown,
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="column"] > div > div {
  border-radius: var(--clay-radius);
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--clay-surface);
  box-shadow: var(--clay-shadow);
  border: 1px solid rgba(124, 111, 240, 0.10);
}

/* Metrics: rounded clay tiles */
[data-testid="stMetric"] {
  background: var(--clay-surface);
  border-radius: 22px;
  padding: 18px 20px;
  box-shadow: var(--clay-shadow);
  border: 1px solid rgba(124, 111, 240, 0.10);
}
[data-testid="stMetricValue"] { color: var(--clay-accent); font-weight: 700; }
[data-testid="stMetricLabel"] p { color: var(--clay-muted) !important; }

/* Buttons: pill-shaped, pastel, tactile */
.stButton > button, [data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
  border-radius: 999px !important;
  border: none !important;
  padding: 0.55rem 1.35rem !important;
  font-weight: 600 !important;
  color: #4c44a8 !important;
  background: var(--clay-accent-soft) !important;
  box-shadow: -6px -6px 14px rgba(255,255,255,.9), 8px 9px 18px rgba(124,111,240,.22) !important;
  transition: transform .12s ease, box-shadow .12s ease;
}
.stButton > button:hover, [data-testid="baseButton-primary"]:hover {
  transform: translateY(-2px) scale(1.02);
  color: var(--clay-accent) !important;
}
.stButton > button:active { transform: translateY(0) scale(.98); }
.stButton > button[kind="primary"], [data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #8f83f5, #7c6ff0) !important;
  color: #ffffff !important;
}
.stDownloadButton > button { border-radius: 999px !important; }

/* Inputs and selects: soft inset clay wells */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTimeInput input, .stTextArea textarea, [data-testid="stSelectbox"] > div,
[data-testid="stMultiSelect"] > div, [data-baseweb="select"] > div {
  border-radius: 18px !important;
  border: 1px solid rgba(124, 111, 240, 0.16) !important;
  background: #fbfaff !important;
  box-shadow: inset 4px 4px 9px rgba(124,111,240,.08),
              inset -4px -4px 9px rgba(255,255,255,.9) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--clay-accent) !important;
}

/* Dataframes and tables */
[data-testid="stDataFrame"] {
  border-radius: 20px !important;
  overflow: hidden;
  box-shadow: var(--clay-shadow);
  border: 1px solid rgba(124, 111, 240, 0.10);
}

/* Tabs: rounded clay chips */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 8px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  border-radius: 16px 16px 0 0;
  background: #f1eefc;
  padding: 8px 18px;
}
[data-testid="stTabs"] [aria-selected="true"] {
  background: var(--clay-accent-soft);
  border-radius: 16px 16px 0 0;
}

/* Alerts: soft rounded notes */
[data-testid="stAlert"] {
  border-radius: 20px !important;
  border: 1px solid rgba(124, 111, 240, 0.12);
}

/* Expanders */
[data-testid="stExpander"] {
  border-radius: var(--clay-radius) !important;
  border: 1px solid rgba(124, 111, 240, 0.12) !important;
  background: var(--clay-surface);
  box-shadow: var(--clay-shadow);
}

/* Progress / spinners keep default color; focus outlines stay visible */
a, [data-testid="stSidebar"] a { color: var(--clay-teal); }
:focus-visible { outline: 3px solid var(--clay-accent); outline-offset: 2px; }
</style>
"""


def apply_theme() -> None:
    """Inject the Claymorphism stylesheet (call once after set_page_config)."""
    st.markdown(_CLAY_CSS, unsafe_allow_html=True)
