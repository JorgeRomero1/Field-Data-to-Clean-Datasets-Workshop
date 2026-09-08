"""Shared visual styling for IDataField 2.0.

Colors and radii live in .streamlit/config.toml so native Streamlit widgets
are themed automatically. This module covers what config.toml cannot: the
sidebar navigation styling (streamlit_option_menu renders its own markup and
ignores the theme) and a small CSS layer for the header, buttons, and
containers.

Call apply_theme() once per run from main.py.
"""

import streamlit as st

# Single source of truth for the palette. Mirrors .streamlit/config.toml.
COLORS = {
    "navy": "#204458",
    "navy_dark": "#173242",
    "navy_soft": "#2C5A73",
    "sky": "#ACDCF9",
    "sky_soft": "#E7F1F9",
    "white": "#FFFFFF",
    "gray_bg": "#F4F6F8",
    "gray_line": "#DCE3E9",
    "gray_text": "#5B7183",
}

# Styles passed to streamlit_option_menu.
MENU_STYLES = {
    "container": {
        "padding": "0.25rem 0",
        "background-color": COLORS["navy"],
    },
    "icon": {
        "color": COLORS["sky"],
        "font-size": "0.95rem",
    },
    "nav-link": {
        "color": "#DCE8F0",
        "font-size": "0.88rem",
        "font-weight": "500",
        "text-align": "left",
        "margin": "3px 0",
        "padding": "0.5rem 0.75rem",
        "border-radius": "8px",
        "--hover-color": COLORS["navy_soft"],
    },
    "nav-link-selected": {
        "background-color": COLORS["sky"],
        "color": COLORS["navy"],
        "font-weight": "600",
    },
    "menu-title": {
        "color": COLORS["white"],
        "font-size": "0.8rem",
        "font-weight": "600",
        "letter-spacing": "0.08em",
        "text-transform": "uppercase",
    },
    "menu-icon": {
        "color": COLORS["sky"],
    },
}


def apply_theme():
    """Inject the CSS layer that config.toml cannot express."""
    st.markdown(
        f"""
        <style>
        /* Selectors are doubled up on purpose: Streamlit renames its
           internal classes between releases (.stMainBlockContainer used to
           be .block-container), and this app is run from unpinned installs
           on several machines. Matching both keeps the design intact on
           older versions instead of silently doing nothing. */

        /* Give the working area room to breathe and cap line length. */
        .stMainBlockContainer,
        .main > .block-container {{
            padding-top: 2.2rem;
            padding-bottom: 4rem;
            max-width: 1500px;
        }}

        /* Let the light gray background show through the toolbar strip. */
        [data-testid="stHeader"],
        .stApp > header {{
            background: transparent;
        }}

        /* App title, with the sky accent rule borrowed from the logo.
           Scoped to .stApp rather than the block container so it survives
           the class rename; the sidebar carries no headings of its own. */
        .stApp h1 {{
            color: {COLORS["navy"]};
            font-weight: 700;
            letter-spacing: -0.01em;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid {COLORS["sky"]};
            margin-bottom: 1.6rem;
        }}

        .stApp h2,
        .stApp h3 {{
            color: {COLORS["navy"]};
        }}

        /* Section titles sit at the intro size, set apart by weight alone. */
        .stApp h3 {{
            font-size: 16.5px;
            font-weight: 700;
        }}

        /* Page intros only. Helper captions inside panels keep Streamlit's
           smaller default. */
        .st-key-page_intro [data-testid="stCaptionContainer"] p {{
            font-size: 16.5px;
            line-height: 1.55;
        }}

        /* --- Sidebar --------------------------------------------------- */
        /* Painted here as well as in [theme.sidebar], because that config
           section is ignored by older Streamlit and the sidebar would fall
           back to white, taking the white wordmark down with it. */
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] > div,
        [data-testid="stSidebarContent"],
        [data-testid="stSidebarUserContent"] {{
            background-color: {COLORS["navy"]};
        }}

        [data-testid="stSidebar"] {{
            border-right: 1px solid {COLORS["navy_dark"]};
        }}

        /* Guard against the heading rules above landing on navy. */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {COLORS["white"]};
            border-bottom: none;
        }}
        [data-testid="stSidebar"] .stMarkdown p {{
            color: #C6D6E1;
        }}
        /* The menu icon inherits the sky color, which vanishes on the
           sky-filled selected row. */
        [data-testid="stSidebar"] .nav-link-selected i {{
            color: {COLORS["navy"]} !important;
        }}

        /* The wordmark is drawn as text rather than an image so it sits
           directly on the navy sidebar and stays crisp at any size. */
        .idf-sidebar-brand {{
            text-align: center;
            padding: 0.6rem 0 1.3rem 0;
        }}
        /* Shrink-wrap the wordmark so the rule and version can sit flush with
           its right edge, the way they do in the original logo. */
        .idf-brand-mark {{
            display: inline-block;
            text-align: right;
        }}
        .idf-brand-name {{
            color: {COLORS["white"]};
            font-size: 3rem;
            font-weight: 800;
            line-height: 1.02;
            letter-spacing: -0.02em;
        }}
        .idf-brand-rule {{
            width: 70px;
            height: 4px;
            border-radius: 2px;
            background: {COLORS["sky"]};
            margin: 0.5rem 0 0.3rem auto;
        }}
        /* In the original logo the version matched the wordmark color, so it
           follows the wordmark to white rather than staying navy. */
        .idf-brand-version {{
            color: {COLORS["white"]};
            font-size: 1.25rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}

        /* --- Widgets ---------------------------------------------------- */
        /* Actions in this app are all "load / generate" buttons, so give
           every button the solid navy treatment. */
        .stApp .stButton > button,
        .stApp .stFormSubmitButton > button,
        .stApp [data-testid="stFormSubmitButton"] > button,
        .stApp .stDownloadButton > button {{
            background: {COLORS["navy"]};
            color: {COLORS["white"]};
            border: 1px solid {COLORS["navy"]};
            font-weight: 600;
        }}
        .stApp .stButton > button:hover,
        .stApp .stFormSubmitButton > button:hover,
        .stApp [data-testid="stFormSubmitButton"] > button:hover,
        .stApp .stDownloadButton > button:hover {{
            background: {COLORS["navy_dark"]};
            border-color: {COLORS["navy_dark"]};
            color: {COLORS["white"]};
        }}

        [data-testid="stForm"],
        [data-testid="stFileUploaderDropzone"] {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["gray_line"]};
        }}

        [data-testid="stExpander"] details {{
            background: {COLORS["white"]};
            border: 1px solid {COLORS["gray_line"]};
        }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 0.25rem;
            border-bottom: 1px solid {COLORS["gray_line"]};
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS["navy"]};
            font-weight: 600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def intro(text):
    """Page introduction, larger than the helper captions inside panels."""
    with st.container(key="page_intro"):
        st.caption(text)


def sidebar_brand():
    """Wordmark at the top of the navy sidebar."""
    st.sidebar.markdown(
        """
        <div class="idf-sidebar-brand">
            <div class="idf-brand-mark">
                <div class="idf-brand-name">IData<br>Field</div>
                <div class="idf-brand-rule"></div>
                <div class="idf-brand-version">2.0</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
