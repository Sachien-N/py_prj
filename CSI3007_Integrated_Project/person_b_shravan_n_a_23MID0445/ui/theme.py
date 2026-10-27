"""Glassmorphism design system for Person B's dashboard.

Translucent frosted panels over a controlled indigo gradient, subtle 1px
light borders, restrained backdrop blur, and readable dark-on-light glass
cards. Applied by injecting CSS into Streamlit; no business logic changes.
Blur radii and panel opacity are tuned so text contrast stays accessible.
"""

from __future__ import annotations

import streamlit as st

DESIGN_SYSTEM = "Glassmorphism"

_GLASS_CSS = """
<style>
/* ---------- Glassmorphism · Person B (Shravan N A · 23MID0445) ---------- */
:root {
  --glass-bg-1: #eef2ff;
  --glass-bg-2: #e0e7ff;
  --glass-blob-1: rgba(99, 102, 241, 0.20);
  --glass-blob-2: rgba(14, 165, 233, 0.16);
  --glass-panel: rgba(255, 255, 255, 0.66);
  --glass-border: rgba(255, 255, 255, 0.75);
  --glass-text: #111827;
  --glass-muted: #4b5563;
  --glass-accent: #4f46e5;
  --glass-blur: 14px;
}

/* App background: layered gradient + two soft colour blobs */
html, body, .stApp {
  background:
    radial-gradient(720px 480px at 88% -6%, var(--glass-blob-1), transparent 62%),
    radial-gradient(640px 460px at -8% 102%, var(--glass-blob-2), transparent 60%),
    linear-gradient(150deg, var(--glass-bg-1) 0%, var(--glass-bg-2) 100%) !important;
  background-attachment: fixed !important;
  color: var(--glass-text);
}

header[data-testid="stHeader"] { background: transparent !important; }

/* Sidebar: frosted glass rail */
section[data-testid="stSidebar"] > div {
  background: rgba(255, 255, 255, 0.55) !important;
  backdrop-filter: blur(var(--glass-blur)) saturate(1.25);
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.25);
  border-right: 1px solid var(--glass-border);
}

/* Main content panels: glass cards */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--glass-panel);
  backdrop-filter: blur(var(--glass-blur)) saturate(1.3);
  -webkit-backdrop-filter: blur(var(--glass-blur)) saturate(1.3);
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  box-shadow: 0 10px 30px rgba(67, 56, 202, 0.10),
              inset 0 1px 0 rgba(255, 255, 255, 0.85);
}

/* Metrics: floating glass chips */
[data-testid="stMetric"] {
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: 0 8px 22px rgba(67, 56, 202, 0.10),
              inset 0 1px 0 rgba(255, 255, 255, 0.9);
}
[data-testid="stMetricValue"] { color: var(--glass-accent); font-weight: 700; }
[data-testid="stMetricLabel"] p { color: var(--glass-muted) !important; }

/* Buttons: refined glass pills */
.stButton > button, [data-testid="baseButton-primary"], [data-testid="baseButton-secondary"] {
  border-radius: 14px !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  background: rgba(255, 255, 255, 0.55) !important;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #3730a3 !important;
  font-weight: 600 !important;
  box-shadow: 0 6px 16px rgba(67, 56, 202, 0.14),
              inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
  transition: transform .12s ease, background .12s ease;
}
.stButton > button:hover { background: rgba(255,255,255,.8) !important; transform: translateY(-1px); }
.stButton > button[kind="primary"], [data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  color: #ffffff !important;
  border-color: rgba(255, 255, 255, 0.35) !important;
}
.stDownloadButton > button { border-radius: 14px !important; }

/* Inputs: clear glass wells with visible focus */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTimeInput input, .stTextArea textarea, [data-baseweb="select"] > div {
  border-radius: 14px !important;
  border: 1px solid rgba(99, 102, 241, 0.28) !important;
  background: rgba(255, 255, 255, 0.72) !important;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: var(--glass-text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--glass-accent) !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18) !important;
}

/* Dataframes / tables */
[data-testid="stDataFrame"] {
  border-radius: 16px !important;
  overflow: hidden;
  border: 1px solid var(--glass-border);
  box-shadow: 0 8px 24px rgba(67, 56, 202, 0.10);
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab"] { border-radius: 12px 12px 0 0; }
[data-testid="stTabs"] [aria-selected="true"] {
  background: rgba(255, 255, 255, 0.65);
}

/* Alerts and expanders */
[data-testid="stAlert"] {
  border-radius: 16px !important;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border) !important;
}
[data-testid="stExpander"] {
  border-radius: 18px !important;
  border: 1px solid var(--glass-border) !important;
  background: rgba(255, 255, 255, 0.55) !important;
  backdrop-filter: blur(var(--glass-blur));
  -webkit-backdrop-filter: blur(var(--glass-blur));
}

a { color: var(--glass-accent); }
:focus-visible { outline: 3px solid var(--glass-accent); outline-offset: 2px; }
</style>
"""


def apply_theme() -> None:
    """Inject the Glassmorphism stylesheet (call once after set_page_config)."""
    st.markdown(_GLASS_CSS, unsafe_allow_html=True)
