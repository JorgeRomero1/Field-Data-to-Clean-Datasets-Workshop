import base64
from io import BytesIO
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

import theme

BASE_DIR = Path(__file__).resolve().parent

BANNER_FILE = BASE_DIR / "content" / "welcome_banner_2.jpg"

INTRO = (
    "This app was developed by graduate students to support data collection and "
    "processing for the **Wheat and Forages Lab** at **Kansas State University**. "
    "It provides a structured workflow for organizing experiments, improving "
    "sample traceability, reducing errors, and automating routine tasks. The app "
    "also helps the team track sample processing progress and generate reports."
)

CONTACTS = [
    ("Nico", "ngiordano@ksu.edu", "(785)473-8442"),
    ("Jorge", "jorgeromero@ksu.edu", "(785)571-4081"),
    ("Jazmin", "jgastaldi@ksu.edu", "(785)317-7409"),
]

# Workshop only. Set the link, save the QR into content/, delete when done.
FEEDBACK_URL = ""
FEEDBACK_QR_FILE = BASE_DIR / "content" / "workshop_feedback_qr.png"

STYLE = f"""
<style>
.idf-hero {{
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    min-height: 250px;
    padding: 2rem 2.25rem;
    border-radius: 12px;
    background-size: cover;
    background-position: center 60%;
    color: {theme.COLORS["white"]};
}}
.idf-hero-feedback {{
    flex: 0 0 auto;
    text-align: center;
}}
.idf-hero-feedback img {{
    width: 110px;
    border-radius: 8px;
    display: block;
    background: {theme.COLORS["white"]};
    padding: 6px;
}}
.idf-hero-feedback .idf-hero-label {{
    font-size: 0.78rem;
    letter-spacing: 0.04em;
    margin-bottom: 0.5rem;
    opacity: 0.9;
}}
.idf-hero-feedback a {{
    color: {theme.COLORS["sky"]};
    font-size: 0.78rem;
}}
</style>
"""


@st.cache_data
def _data_uri(path, mime):
    """Inline an image so it can be used inside the hero markup."""
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


@st.cache_data
def _qr_data_uri(path):
    """Crop the exported file down to the code itself, then add a quiet zone."""
    image = Image.open(path).convert("L")

    dark = image.point(lambda value: 255 if value < 128 else 0)
    box = dark.getbbox()

    if box:
        image = image.crop(box)

    padding = max(4, round(min(image.size) * 0.08))
    image = ImageOps.expand(image, border=padding, fill=255)

    buffer = BytesIO()
    image.save(buffer, "PNG")

    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"


def app():
    st.markdown(STYLE, unsafe_allow_html=True)

    theme.intro(INTRO)

    _hero()

    st.divider()

    _contacts()


def _hero():
    """Banner photo, darkened only when the feedback QR sits on top of it."""
    if not BANNER_FILE.exists():
        return

    photo = _data_uri(BANNER_FILE, "image/jpeg")

    feedback = ""
    scrim = ""

    if FEEDBACK_QR_FILE.exists() or FEEDBACK_URL:
        scrim = "linear-gradient(rgba(23, 50, 66, 0.55), rgba(23, 50, 66, 0.55)), "
        qr = ""
        link = ""

        if FEEDBACK_QR_FILE.exists():
            qr = f'<img src="{_qr_data_uri(FEEDBACK_QR_FILE)}" alt="Feedback QR code">'

        if FEEDBACK_URL:
            link = f'<div><a href="{FEEDBACK_URL}">Give feedback</a></div>'

        feedback = (
            '<div class="idf-hero-feedback">'
            '<div class="idf-hero-label">Workshop feedback</div>'
            f"{qr}{link}</div>"
        )

    st.markdown(
        f'<div class="idf-hero" style="background-image: {scrim}url({photo});">'
        f"{feedback}</div>",
        unsafe_allow_html=True,
    )


def _contacts():
    """Contacts stacked under the heading, one person per line."""
    entries = "".join(
        f'<div style="white-space:nowrap;">{name} '
        f'(<a href="mailto:{email}">{email}</a> · {phone})</div>'
        for name, email, phone in CONTACTS
    )

    st.markdown(
        f'<div style="font-size:16.5px;line-height:1.7;'
        f'color:{theme.COLORS["gray_text"]};">'
        f'<strong>Need help?</strong>{entries}</div>',
        unsafe_allow_html=True,
    )
