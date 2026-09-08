from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx
import theme


BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"

DISPLAY_COLUMNS = ["TRIAL_SHORT", "LOC_SHORT", "YEAR", "SAMPLING", "Plot", "LABEL"]

INTRO = """
Select the trial parameters and label settings to generate printable QR code labels.
"""

# Dimensions come from label_generator, which still takes BIG / SMALL.
SIZE_LABELS = {
    "BIG": "Big (3.9 × 2.4 in)",
    "SMALL": "Small (3.5 × 1.4 in)",
}


def app():
    st.title("Generate Bag Labels")

    theme.intro(INTRO)

    # Check metadata file
    if not LABELS_FILE.is_file():
        st.error("Labels.csv was not found in the metadata folder.")
        return

    # Load labels
    metadata = pd.read_csv(LABELS_FILE)
    labels = fx.explode_labels(metadata)

    # Remove duplicated labels
    labels = labels.drop_duplicates(subset=["LABEL"]).reset_index(drop=True)

    # -------------------------------------------------------------
    # Filters
    # -------------------------------------------------------------

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        year_options = sorted(labels["YEAR"].dropna().unique())
        YEAR = st.selectbox("Year", year_options)

    with col2:
        trial_options = sorted(labels.loc[labels["YEAR"] == YEAR, "TRIAL_SHORT"].dropna().unique())
        TRIAL = st.multiselect("Trial", trial_options)

    with col3:
        location_options = sorted(labels.loc[(labels["YEAR"] == YEAR) & (labels["TRIAL_SHORT"].isin(TRIAL)), "LOC_SHORT"].dropna().unique())
        LOCATION = st.multiselect("Location", location_options)

    with col4:
        sampling_options = sorted(labels.loc[(labels["YEAR"] == YEAR) & (labels["TRIAL_SHORT"].isin(TRIAL)) & (labels["LOC_SHORT"].isin(LOCATION)), "SAMPLING"].dropna().unique())
        SAMPLING = st.multiselect("Sampling", sampling_options)

    with col5:
        SIZE = st.selectbox("Label size", list(SIZE_LABELS), format_func=lambda size: SIZE_LABELS[size])

    # -------------------------------------------------------------
    # Filter labels
    # -------------------------------------------------------------

    idx = (
        (labels["YEAR"] == YEAR) & labels["TRIAL_SHORT"].isin(TRIAL) & 
        labels["LOC_SHORT"].isin(LOCATION) & labels["SAMPLING"].isin(SAMPLING)
        )

    filtered_labels = labels.loc[idx, DISPLAY_COLUMNS].drop_duplicates(subset=["LABEL"]).reset_index(drop=True)

    # -------------------------------------------------------------
    # Preview
    # -------------------------------------------------------------

    if TRIAL and LOCATION and SAMPLING:

        st.write(f"**{len(filtered_labels)} labels selected**")
        st.dataframe(filtered_labels, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------
    # File settings
    # -------------------------------------------------------------

    FILENAME = st.text_input("Name of the label file")

    ready_to_generate = bool(TRIAL and LOCATION and SAMPLING and FILENAME.strip() and not filtered_labels.empty)

    # Clear old download if selections change
    selection_key = (YEAR, tuple(TRIAL), tuple(LOCATION), tuple(SAMPLING), SIZE, FILENAME)

    if st.session_state.get("_label_selection_key") != selection_key:
        st.session_state["_label_selection_key"] = selection_key
        st.session_state.pop("_label_pdf", None)
        st.session_state.pop("_label_pdf_name", None)

    # -------------------------------------------------------------
    # Generate labels
    # -------------------------------------------------------------

    if st.button("Generate bag labels", disabled=not ready_to_generate):

        try:
            out_filepath = fx.label_output_directory(YEAR, BASE_DIR)
            pdf_path = fx.label_generator(filtered_labels, SIZE, FILENAME, out_filepath)

            with open(pdf_path, "rb") as pdf_file:
                st.session_state["_label_pdf"] = pdf_file.read()

            st.session_state["_label_pdf_name"] = pdf_path.name
            st.success(f"{len(filtered_labels)} labels generated successfully.")

        except Exception as error:
            st.error(f"Labels could not be generated: {error}")

    # -------------------------------------------------------------
    # Download
    # -------------------------------------------------------------

    if "_label_pdf" in st.session_state:
        st.download_button("Download labels", data=st.session_state["_label_pdf"], file_name=st.session_state["_label_pdf_name"], mime="application/pdf")

    # -------------------------------------------------------------
    # Optional complete dataset
    # -------------------------------------------------------------

    with st.expander("View all available labels"):
        st.dataframe(labels[DISPLAY_COLUMNS], use_container_width=True, hide_index=True)