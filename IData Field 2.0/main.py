import activities, dataupload_other_data, labels, canopy_cover, seeds, merge_data, labels_stakes, welcome, field_data_uploader, metadata, combine, protein_data_uploader, uploadPartitioning, data_progress, reports
import streamlit as st
from streamlit_option_menu import option_menu
from PIL import Image

import theme


im = Image.open("content/wheat.png")
st.set_page_config(page_title="IDataField2.0", page_icon=im, layout="wide")

PAGES = {
    "Welcome!": welcome,
    "Metadata": metadata,
    "Data Progress": data_progress,
    "Activity Dates Uploader": activities,

    "Partitioning": uploadPartitioning,
    "Plant Height": field_data_uploader,
    "Seed Counter": seeds,
    "Protein": protein_data_uploader,
    "Combine": combine,

    "Lab Data Uploader": dataupload_other_data,
    "Imagery & Canopy Cover": canopy_cover,
    "Bag Label Generator": labels,
    "Stake Label Generator": labels_stakes,

    "Merge Datasets": merge_data,
    "Reports": reports,
    }

MENU_OPTIONS = [
    "Welcome!",
    "Metadata",
    "Data Progress",
    "Activity Dates Uploader",

    "---",

    "Partitioning",
    "Plant Height",
    "Seed Counter",
    "Protein",
    "Combine",

    "---",

    "Lab Data Uploader",
    "Imagery & Canopy Cover",
    "Bag Label Generator",
    "Stake Label Generator",

    "---",

    "Merge Datasets",
    "Reports"
    ]


ICONS = [
    "house",
    "database",
    "clipboard-check",
    "calendar-event",

    "dash-lg",

    "box-arrow-in-down",
    "rulers",
    "upc-scan",
    "box-arrow-in-down",
    "gear",

    "dash-lg",

    "box-arrow-in-down",
    "badge-cc-fill",
    "qr-code",
    "qr-code",

    "dash-lg",

    "union",
    "file-earmark-text",
    ]

assert len(ICONS) == len(MENU_OPTIONS), "MENU_OPTIONS and ICONS must stay the same length"

theme.apply_theme()
theme.sidebar_brand()

with st.sidebar:
    selection = option_menu(menu_title="Menu", options=MENU_OPTIONS, icons=ICONS, menu_icon="three-dots", styles=theme.MENU_STYLES)

if selection == "Welcome!":
    st.title("Welcome to IDataField 2.0")

page = PAGES[selection]
page.app()