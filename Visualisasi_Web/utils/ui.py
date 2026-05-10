from contextlib import contextmanager
from html import escape

import streamlit as st


def apply_dashboard_styles():
    """Inject custom Streamlit CSS for consistent page, sidebar, and card styling."""
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #f4f7fb 0%, #e8eef9 100%);
        }

        .main .block-container {
            padding-top: 2.2rem;
            padding-bottom: 2rem;
            max-width: 1350px;
        }

        [data-testid="stSidebar"] {
            min-width: 250px;
            max-width: 250px;
            background: linear-gradient(180deg, #0f2742 0%, #173e67 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: #f7fbff;
        }

        [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        [data-testid="stSidebarNav"] a {
            border-radius: 14px;
            margin-bottom: 0.25rem;
        }

        [data-testid="stSidebarNav"] a:hover {
            background-color: rgba(255, 255, 255, 0.1);
        }

        .dashboard-hero {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 39, 66, 0.12);
            border-radius: 24px;
            box-shadow: 0 18px 40px rgba(15, 39, 66, 0.08);
        }

        .dashboard-hero {
            padding: 1.8rem 1.9rem;
            margin: 1rem 0 1.5rem 0;
        }

        .dashboard-hero h2 {
            color: #12304f;
            margin-bottom: 0.75rem;
        }

        .dashboard-hero p,
        .dashboard-hero li {
            color: #3b4f68;
            line-height: 1.7;
            font-size: 1rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 39, 66, 0.12);
            border-radius: 24px;
            box-shadow: 0 18px 40px rgba(15, 39, 66, 0.08);
            padding: 0.95rem 1rem 0.35rem 1rem;
            margin-bottom: 1.25rem;
        }

        .chart-card-header h3 {
            color: #12304f;
            font-size: 1.05rem;
            margin: 0 0 0.3rem 0;
        }

        .chart-card-header p {
            color: #5b6f86;
            margin: 0.35rem 0 1rem 0;
            font-size: 0.92rem;
        }

        div[data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(15, 39, 66, 0.12);
            border-radius: 18px;
            box-shadow: 0 10px 26px rgba(15, 39, 66, 0.06);
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
