from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx


BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"


def app():

    st.title("Process Combine Yield Data")

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    if not LABELS_FILE.is_file():
        st.error("Labels.csv was not found in the metadata folder.")
        return

    metadata = pd.read_csv(LABELS_FILE)
    labels = fx.explode_labels(metadata)

    # ------------------------------------------------------------------
    # Select field
    # ------------------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        YEAR = st.selectbox("YEAR", sorted(labels["YEAR"].dropna().unique()))

    with col2:
        location_options = sorted(labels.loc[labels["YEAR"] == YEAR, "LOC_SHORT"].dropna().unique())
        LOCATION = st.selectbox("LOCATION", location_options)

    with col3:
        LENGTH = st.number_input("Default plot length (m)", value=8.50, step=0.01)

    with col4:
        STD_MOIST = st.number_input("Standard grain trading moisture (%)", value=13.5, step=0.01)

    NROW = st.number_input("Default number of rows in the planter", value=7, min_value=1, step=1)

    # ------------------------------------------------------------------
    # Expected trials and plots
    # ------------------------------------------------------------------

    field_labels = labels[(labels["YEAR"] == YEAR) & (labels["LOC_SHORT"] == LOCATION)].copy()
    field_labels = field_labels[["YEAR", "LOC_SHORT", "TRIAL_SHORT", "Plot"]].drop_duplicates()
    field_labels.columns = ["YEAR", "LOCATION", "TRIAL", "PLOT"]

    TRIALS = field_labels["TRIAL"].unique().tolist()

    if not TRIALS:
        st.warning(f"No trials were found for {LOCATION} in year {YEAR}.")
        return

    st.caption(f"Trials at {LOCATION}: {', '.join(TRIALS)}")

    # ------------------------------------------------------------------
    # Upload combine data
    # ------------------------------------------------------------------

    upload = st.file_uploader("Upload combine data - One field at a time", type=["csv"])

    if upload is None:
        return

    # ------------------------------------------------------------------
    # Read combine data
    # ------------------------------------------------------------------

    try:
        combine = pd.read_csv(upload)
        combine = combine.filter(regex="RANGE|ROW|TRIAL|PLOT|Weight|Moisture|Test Weight")
        combine.columns = ["RANGE", "ROW", "TRIAL", "PLOT", "Weight", "Moisture", "Test Weight"]

        combine["PLOT"] = pd.to_numeric(combine["PLOT"], errors="coerce")
        combine = combine[combine["TRIAL"].isin(TRIALS)].copy()

    except Exception as error:
        st.error(f"Could not read combine file: {error}")
        return

    if combine.empty:
        st.error("No combine observations match the trials at the selected location.")
        return

    # ------------------------------------------------------------------
    # Check duplicated observations
    # ------------------------------------------------------------------

    duplicate_combine = combine.duplicated(subset=["TRIAL", "PLOT"], keep=False)

    if duplicate_combine.any():
        st.error("Duplicated Trial + Plot combinations were found in the combine file.")

        with st.expander("View duplicated combine observations", expanded=True):
            st.dataframe(combine.loc[duplicate_combine].sort_values(["TRIAL", "PLOT"]), use_container_width=True, hide_index=True)

        return

    # ------------------------------------------------------------------
    # Default plot dimensions
    # ------------------------------------------------------------------

    combine["PLOT_LENGTH"] = LENGTH
    combine["ROWS"] = NROW

    # ------------------------------------------------------------------
    # Optional plot length adjustment
    # ------------------------------------------------------------------

    MODIFY_LENGTH = st.checkbox("Modify plot length based on orthophoto")

    if MODIFY_LENGTH:

        st.caption("Modify plot length or harvested rows where needed.")

        combine = st.data_editor(combine, use_container_width=True, num_rows="fixed", hide_index=True, disabled=["RANGE", "ROW", "TRIAL", "PLOT", "Weight", "Moisture", "Test Weight"], column_config={"PLOT_LENGTH": st.column_config.NumberColumn("Plot length (m)", format="%.2f"), "ROWS": st.column_config.NumberColumn("Rows", format="%d")})

    else:
        st.info(f"Using default plot length of {LENGTH:.2f} m and {NROW} rows.")

    # ------------------------------------------------------------------
    # Process trials
    # ------------------------------------------------------------------

    processed_trials = {}

    for trial in TRIALS:

        expected = field_labels[field_labels["TRIAL"] == trial].copy()
        observed = combine[combine["TRIAL"] == trial].copy()

        expected["PLOT"] = pd.to_numeric(expected["PLOT"], errors="coerce")
        observed["PLOT"] = pd.to_numeric(observed["PLOT"], errors="coerce")

        trial_data = pd.merge(expected, observed, on=["TRIAL", "PLOT"], how="left")

        # --------------------------------------------------------------
        # Your existing yield calculations
        # --------------------------------------------------------------

        trial_data["AREA"] = trial_data["PLOT_LENGTH"].astype(float) * trial_data["ROWS"].astype(float) / float(NROW) * 0.3048 * 6

        trial_data["W13"] = trial_data["Weight"].astype(float) * (100 - trial_data["Moisture"].astype(float)) / (100 - STD_MOIST)
        trial_data["W0"] = trial_data["W13"] * (1 - STD_MOIST / 100)

        trial_data["Yield Std Moist (kg/ha)"] = trial_data["W13"] / trial_data["AREA"] * 10000
        trial_data["Yield Dry Basis (kg/ha)"] = trial_data["W0"] / trial_data["AREA"] * 10000

        trial_data["Yield Std Moist (bu/ac)"] = trial_data["W13"] / trial_data["AREA"] * 0.0149 * 10000
        trial_data["Yield Dry Basis (bu/ac)"] = trial_data["W0"] / trial_data["AREA"] * 0.0149 * 10000

        trial_data["TW (kg/hL)"] = trial_data["Test Weight"]

        processed_trials[trial] = trial_data

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    st.subheader("Data to upload")

    for trial, trial_data in processed_trials.items():

        expected_n = len(trial_data)
        observed_n = trial_data["Weight"].notna().sum()

        if observed_n == expected_n:
            st.success(f"{trial}: {observed_n}/{expected_n} plots matched.")
        else:
            st.warning(f"{trial}: {observed_n}/{expected_n} plots matched. Check missing plots before uploading.")

        with st.expander(f"Preview {trial}"):
            preview_columns = ["LOCATION", "TRIAL", "PLOT", "Yield Dry Basis (kg/ha)", "TW (kg/hL)", "Moisture"]
            st.dataframe(trial_data[preview_columns], use_container_width=True, hide_index=True)

    # ------------------------------------------------------------------
    # Upload mode
    # ------------------------------------------------------------------

    UPLOAD_MODE = st.radio("How should existing combine data be handled?", ["Fill empty plots only", "Overwrite existing combine data"], index=0)

    # ------------------------------------------------------------------
    # Upload to trial CSV
    # ------------------------------------------------------------------

    if st.button("UPLOAD COMBINE DATA"):

        try:

            total_updated = 0
            total_skipped = 0

            for trial, trial_data in processed_trials.items():

                filename = fx.get_trial_file(trial, YEAR, BASE_DIR)

                valid_data = trial_data[trial_data["Weight"].notna()].copy()

                updated, skipped = fx.upload_combine_to_trial(valid_data, filename, LOCATION, overwrite=UPLOAD_MODE == "Overwrite existing combine data")

                total_updated += updated
                total_skipped += skipped

            st.success(f"{total_updated} plots were updated successfully.")

            if total_skipped > 0:
                st.info(f"{total_skipped} plots already contained combine data and were not changed.")

        except Exception as error:
            st.error(f"Combine data could not be uploaded: {error}")