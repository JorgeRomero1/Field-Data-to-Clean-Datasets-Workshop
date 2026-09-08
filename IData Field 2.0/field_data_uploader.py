from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx
import theme


BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"

PLANT_HEIGHT_COLUMNS = ["PlantHeight1_cm", "PlantHeight2_cm", "PlantHeight3_cm", "PlantHeight4_cm", "PlantHeight5_cm"]

INTRO = """
Filter by season, trial, and location to load the plot list, then enter individual plant height measurements in centimeters (cm) directly into the table.
"""

TABLE_NOTE = "Type individual plant height readings in centimeters (cm) directly into the cells for each plot row."


def app():

    st.title("Plant Height Data Entry")

    theme.intro(INTRO)

    # -------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------

    if not LABELS_FILE.is_file():
        st.error("Labels.csv was not found in the metadata folder.")
        return

    metadata = pd.read_csv(LABELS_FILE)

    # -------------------------------------------------------------
    # Select experiment
    # -------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        YEAR = st.selectbox("Season (harvest year)", sorted(metadata["YEAR"].dropna().unique()), help="Select the harvest year to filter the available trials and locations.")

    with col2:
        trial_options = sorted(metadata.loc[metadata["YEAR"] == YEAR, "TRIAL_SHORT"].dropna().unique())
        TRIAL = st.selectbox("Trial", trial_options, help="Select the specific trial name to load the corresponding plot dataset.")

    with col3:
        location_options = sorted(metadata.loc[(metadata["YEAR"] == YEAR) & (metadata["TRIAL_SHORT"] == TRIAL), "LOC_SHORT"].dropna().unique())
        LOCATION = st.selectbox("Location", location_options, help="Select the field site or location code.")

    # -------------------------------------------------------------
    # Load complete trial file
    # -------------------------------------------------------------

    try:
        filename = fx.get_trial_file(TRIAL, YEAR, BASE_DIR)
        trial_data = pd.read_csv(filename)

    except (FileNotFoundError, pd.errors.ParserError) as error:
        st.error(str(error))
        return

    # -------------------------------------------------------------
    # Check plant height columns
    # -------------------------------------------------------------

    missing_columns = [column for column in PLANT_HEIGHT_COLUMNS if column not in trial_data.columns]

    if missing_columns:
        st.error(f"The trial file is missing these columns: {', '.join(missing_columns)}")
        return

    # -------------------------------------------------------------
    # Select location rows
    # -------------------------------------------------------------

    location_data = trial_data[trial_data["Site"].astype(str) == str(LOCATION)].copy()

    if location_data.empty:
        st.error(f"Location {LOCATION} was not found in {TRIAL}_trial.csv.")
        return

    # -------------------------------------------------------------
    # Data editor
    # -------------------------------------------------------------

    ID_COLUMNS = ["Trial", "Site", "Year", "Plot"]
    display_columns = ID_COLUMNS + PLANT_HEIGHT_COLUMNS

    editor_data = location_data[display_columns].sort_values("Plot").reset_index(drop=True)

    with st.form("plant_height_form"):

        st.caption(TABLE_NOTE)

        edited = st.data_editor(editor_data, use_container_width=True, num_rows="fixed", hide_index=True, disabled=ID_COLUMNS, column_config={column: st.column_config.NumberColumn(format="%.1f") for column in PLANT_HEIGHT_COLUMNS})

        submit = st.form_submit_button("Save plant height data")

    # -------------------------------------------------------------
    # Save only when user confirms
    # -------------------------------------------------------------

    if submit:

        try:
            fx.update_trial_measurements(filename, edited, PLANT_HEIGHT_COLUMNS)
            st.success(f"Plant height data for {TRIAL} - {LOCATION} were saved successfully.")

        except Exception as error:
            st.error(f"Error saving plant height data: {error}")

    # -------------------------------------------------------------
    # Current data
    # -------------------------------------------------------------

    with st.expander("View complete trial file"):
        st.dataframe(trial_data, use_container_width=True, hide_index=True)