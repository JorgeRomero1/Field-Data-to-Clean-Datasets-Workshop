from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx


BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"

NIR_COLUMNS = {
    "Protein Dry basis %, NIR": "GrainProtein_%",
    "Moisture %, NIR": "GrainProteinMoisture_%"
}


def app():

    st.title("Upload Grain Protein Concentration")

    # -------------------------------------------------------------
    # Metadata
    # -------------------------------------------------------------

    if not LABELS_FILE.is_file():
        st.error("Labels.csv was not found in the metadata folder.")
        return

    metadata = pd.read_csv(LABELS_FILE)

    # -------------------------------------------------------------
    # Upload NIR file
    # -------------------------------------------------------------

    upload_data = st.file_uploader("Upload data from NIR", type=["csv", "xlsx"])

    if upload_data is None:
        return

    try:
        if upload_data.name.lower().endswith(".csv"):
            nir_data = pd.read_csv(upload_data)
        else:
            nir_data = pd.read_excel(upload_data)

    except Exception as error:
        st.error(f"Could not read NIR file: {error}")
        return

    # -------------------------------------------------------------
    # Check required NIR columns
    # -------------------------------------------------------------

    required_columns = ["Sample ID"] + list(NIR_COLUMNS.keys())
    missing_columns = [column for column in required_columns if column not in nir_data.columns]

    if missing_columns:
        st.error(f"NIR file is missing these columns: {', '.join(missing_columns)}")
        return

    nir_data["Sample ID"] = nir_data["Sample ID"].astype(str).str.strip()

    # -------------------------------------------------------------
    # Parse Sample ID
    # -------------------------------------------------------------

    try:
        parsed = nir_data["Sample ID"].str.split("-", expand=True)

        if parsed.shape[1] != 5:
            raise ValueError("Some Sample IDs do not follow TRIAL-SITE-YEAR-SAMPLING-PLOT.")

        parsed.columns = ["Trial", "Site", "Year", "Sampling", "Plot"]

        nir_data["Trial"] = parsed["Trial"]
        nir_data["Site"] = parsed["Site"]
        nir_data["Year"] = pd.to_numeric(parsed["Year"], errors="coerce")
        nir_data["Sampling"] = parsed["Sampling"]
        nir_data["Plot"] = pd.to_numeric(parsed["Plot"], errors="coerce")

    except Exception as error:
        st.error(f"Sample IDs could not be read: {error}")
        return

    # -------------------------------------------------------------
    # Experiment selection
    # -------------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        YEAR = st.selectbox("Season (harvest year)", sorted(metadata["YEAR"].dropna().unique()))

    with col2:
        trial_options = sorted(metadata.loc[metadata["YEAR"] == YEAR, "TRIAL_SHORT"].dropna().unique())
        TRIAL = st.selectbox("Trial", trial_options)

    # -------------------------------------------------------------
    # Filter NIR data to selected experiment
    # -------------------------------------------------------------

    experiment_nir = nir_data[(nir_data["Trial"] == TRIAL) & (nir_data["Year"] == int(YEAR))].copy()

    if experiment_nir.empty:
        st.warning(f"No samples for {TRIAL} - {YEAR:02d} were found in the uploaded NIR file.")
        return

    # -------------------------------------------------------------
    # Duplicate Sample IDs
    # -------------------------------------------------------------

    duplicate_mask = experiment_nir["Sample ID"].duplicated(keep=False)
    duplicates = experiment_nir.loc[duplicate_mask].sort_values("Sample ID")

    if not duplicates.empty:
        st.error(f"{duplicates['Sample ID'].nunique()} duplicated Sample ID(s) were found. Remove or resolve duplicates before uploading.")

        with st.expander("View duplicated samples", expanded=True):
            st.dataframe(duplicates[["Sample ID"] + list(NIR_COLUMNS.keys())], use_container_width=True, hide_index=True)

        return

    # -------------------------------------------------------------
    # Load trial file
    # -------------------------------------------------------------

    try:
        filename = fx.get_trial_file(TRIAL, YEAR, BASE_DIR)
        trial_data = pd.read_csv(filename)

    except (FileNotFoundError, pd.errors.ParserError) as error:
        st.error(str(error))
        return

    # -------------------------------------------------------------
    # Check required columns in trial file
    # -------------------------------------------------------------

    missing_trial_columns = [column for column in NIR_COLUMNS.values() if column not in trial_data.columns]

    if missing_trial_columns:
        st.error(f"{TRIAL}_trial.csv is missing these columns: {', '.join(missing_trial_columns)}")
        return

    # -------------------------------------------------------------
    # Match NIR samples with trial plots
    # -------------------------------------------------------------

    trial_keys = trial_data[["Site", "Year", "Plot"]].copy()
    trial_keys["Site"] = trial_keys["Site"].astype(str)
    trial_keys["Year"] = pd.to_numeric(trial_keys["Year"], errors="coerce")
    trial_keys["Plot"] = pd.to_numeric(trial_keys["Plot"], errors="coerce")

    experiment_nir["Site"] = experiment_nir["Site"].astype(str)

    matched = experiment_nir.merge(trial_keys, on=["Site", "Year", "Plot"], how="left", indicator=True)

    unmatched = matched[matched["_merge"] == "left_only"]

    if not unmatched.empty:
        st.warning(f"{len(unmatched)} NIR sample(s) were not found in {TRIAL}_trial.csv.")

        with st.expander("View unmatched samples"):
            st.dataframe(unmatched[["Sample ID", "Site", "Year", "Plot"]], use_container_width=True, hide_index=True)

    valid_nir = experiment_nir.merge(trial_keys, on=["Site", "Year", "Plot"], how="inner")

    if valid_nir.empty:
        st.error("None of the uploaded NIR samples match the selected experiment.")
        return

   # -------------------------------------------------------------
# Check existing protein values
# -------------------------------------------------------------

    protein_columns = list(NIR_COLUMNS.values())

    existing_rows = trial_data.merge(valid_nir[["Site", "Year", "Plot"]].drop_duplicates(), on=["Site", "Year", "Plot"], how="inner")

    existing_mask = existing_rows[protein_columns].notna().any(axis=1)

    existing_count = int(existing_mask.sum())
    empty_count = int((~existing_mask).sum())


    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Matched samples", len(valid_nir))

    with col2:
        st.metric("Empty samples", empty_count)

    with col3:
        st.metric("Existing protein data", existing_count)


    # -------------------------------------------------------------
    # Upload mode
    # -------------------------------------------------------------

    UPLOAD_MODE = st.radio("How should existing protein data be handled?", ["Fill empty samples only", "Overwrite existing protein data"], index=0)


    # -------------------------------------------------------------
    # Preview
    # -------------------------------------------------------------

    preview_columns = ["Sample ID", "Site", "Plot"] + list(NIR_COLUMNS.keys())

    with st.expander("Preview data to upload", expanded=True):
        st.dataframe(valid_nir[preview_columns], use_container_width=True, hide_index=True)


    # -------------------------------------------------------------
    # Upload
    # -------------------------------------------------------------

    if st.button("UPLOAD PROTEIN DATA"):

        try:

            if UPLOAD_MODE == "Fill empty samples only":
                updated, skipped = fx.upload_nir_to_trial(trial_data, valid_nir, filename, NIR_COLUMNS, overwrite=False)
                st.success(f"{updated} empty samples were updated.")

                if skipped > 0:
                    st.info(f"{skipped} samples already contained protein data and were not changed.")

            else:
                if existing_count > 0:
                    st.session_state["_protein_bulk_pending"] = {"TRIAL": TRIAL, "YEAR": YEAR}
                else:
                    updated, skipped = fx.upload_nir_to_trial(trial_data, valid_nir, filename, NIR_COLUMNS, overwrite=True)
                    st.success(f"{updated} protein samples were uploaded successfully.")

        except Exception as error:
            st.error(f"Protein data could not be uploaded: {error}")

    # -------------------------------------------------------------
    # Confirm overwrite
    # -------------------------------------------------------------

    pending = st.session_state.get("_protein_bulk_pending")

    if pending is not None and pending["TRIAL"] == TRIAL and pending["YEAR"] == YEAR:

        st.warning(f"{existing_count} existing protein records will be overwritten.", icon="⚠️")

        if st.button("CONTINUE AND OVERWRITE"):

            try:
                updated, skipped = fx.upload_nir_to_trial(trial_data, valid_nir, filename, NIR_COLUMNS, overwrite=True)
                st.session_state.pop("_protein_bulk_pending", None)
                st.success(f"{updated} protein samples were uploaded successfully.")

            except Exception as error:
                st.error(f"Protein data could not be uploaded: {error}")