from contextlib import contextmanager
from html import escape

import streamlit as st

PALETTE = ["#FAA275", "#FF8C61", "#CE6A85", "#985277", "#5C374C"]
PALETTE_SCALE = [
    [0.0, "#FAA275"],
    [0.25, "#FF8C61"],
    [0.5, "#CE6A85"],
    [0.75, "#985277"],
    [1.0, "#5C374C"],
]


def apply_dashboard_styles():
    """Inject custom Streamlit CSS for consistent page, sidebar, and card styling."""
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #fff7f2 0%, #f7edf4 55%, #f2e8ef 100%);
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1350px;
        }

        [data-testid="stSidebar"] {
            min-width: 200px;
            max-width: 200px;
            background: linear-gradient(180deg, #5c374c 0%, #985277 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        [data-testid="stSidebar"] * {
            color: #fff5f2;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 10px;
            margin-bottom: 0.25rem;
        }

        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }

        [data-testid="stHorizontalBlock"] {
            gap: 0.5rem !important;
        }

        .dashboard-hero {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(152, 82, 119, 0.22);
            border-radius: 10px;
            box-shadow: 0 18px 40px rgba(92, 55, 76, 0.08);
        }

        .dashboard-hero {
            padding: 1.8rem 1.9rem;
            margin: 1rem 0 1.5rem 0;
        }

        .dashboard-hero h2 {
            color: #5c374c;
            margin-bottom: 0.75rem;
        }

        .dashboard-hero p,
        .dashboard-hero li {
            color: #6a3f57;
            line-height: 1.7;
            font-size: 1rem;
        }

        .chart-card-header h3 {
            color: #5c374c;
            font-size: 1.05rem;
            margin: 0 0 0.3rem 0;
        }

        .chart-card-header p {
            color: #7f5368;
            margin: 0.35rem 0 1rem 0;
            font-size: 0.92rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 8px 18px rgba(92, 55, 76, 0.08);
            border-color: rgba(152, 82, 119, 0.28);
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(152, 82, 119, 0.24);
            border-radius: 10px;
            box-shadow: 0 10px 26px rgba(92, 55, 76, 0.06);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@contextmanager
def chart_card(title, description=None):
    """Wrap Streamlit chart content inside a styled dashboard card container."""
    with st.container(border=True):
        description_html = (
            f"<p>{escape(description)}</p>" if description else ""
        )
        st.markdown(
            f"""
            <div class="chart-card-header">
                <h3>{escape(title)}</h3>
                {description_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        yield


def style_figure(fig, margin=None):
    """Apply shared Plotly styling used across dashboard figures."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,247,242,0.9)",
        font=dict(color="#5C374C"),
        margin=margin or dict(l=10, r=10, t=40, b=10),
    )
    return fig
