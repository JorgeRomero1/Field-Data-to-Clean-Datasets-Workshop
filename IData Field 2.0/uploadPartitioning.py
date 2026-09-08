from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx
import theme

INTRO = """
Scan the QR code on your plot label to automatically load the correct trial, location, year, and plot number. Once loaded, enter the whole plant weight along with the individual component measurements (head weight, head number, and stover weight) in grams to update the trial dataset.
"""

TRAIT_NAMES = [
    "WholePlantWeight_g",
    "HeadWeight_g",
    "HeadNumber_No",
    "StoverWeight_g",
    ]

WEIGHT_TOLERANCE = 2.0

BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"


def app():
    st.title("Biomass Partitioning Data Entry")

    theme.intro(INTRO)

    ID = st.text_input("Scan QR code on label",key="ID")

    if not ID:
        st.info("Scan a QR code to start.")
        return

    previous_ID = st.session_state.get("_partitioning_last_ID")

    if previous_ID != ID:
        fx.reset_measurement_inputs()

        st.session_state["_partitioning_last_ID"] = ID

    # Parse QR
    try:
        qr = fx.parse_qr_code(ID)

    except ValueError as error:
        st.error(str(error))
        return

    # Find trial file
    filename = fx.directory_check_trial(qr,BASE_DIR)

    # Load trial
    try:
        dataAll = fx.load_or_create_trial(filename, qr, LABELS_FILE, TRAIT_NAMES)

    except (
        ValueError,
        FileNotFoundError,
        pd.errors.ParserError) as error:
        st.error(str(error))
        return

    # Find plot
    try:
        row_index = fx.find_plot(dataAll, qr["Site"], qr["Plot"])

    except ValueError as error:
        st.error(str(error))
        return

    # Sample information
    st.markdown(
        f"""
        **Trial:** {qr["Trial"]} &nbsp;&nbsp;
        **Site:** {qr["Site"]} &nbsp;&nbsp;
        **Plot:** {qr["Plot"]}
        """
        )

    display_columns = ["Trial", "Year", "Site", "Plot", *TRAIT_NAMES]

    st.dataframe(dataAll.loc[[row_index],display_columns], use_container_width=True, hide_index=True)

    # Data entry
    with st.form("partitioning_form"):

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            WholePlantWeight_g = st.number_input("Whole plant weight (g)", min_value=0.0, step=0.1, format="%.1f", key="WholePlantWeight_input", help="Enter the total weight of the whole plant in grams (g).")

        with col2:
            HeadWeight_g = st.number_input( "Head weight (g)", min_value=0.0, step=0.1, format="%.1f", key="HeadWeight_input", help="Enter the weight of all heads in grams (g).")

        with col3:
            HeadNumber_No = st.number_input("Head number", min_value=0, step=1, key="HeadNumber_input", help="Enter the total count of individual heads.")

        with col4:
            StoverWeight_g = st.number_input( "Stover weight (g)", min_value=0.0, step=0.1, format="%.1f", key="StoverWeight_input", help="Enter the weight of the stover in grams (g).")

        submitted = st.form_submit_button("LOAD DATAPOINT")

    # Process submission
    if submitted:

        trait_values = {
            "WholePlantWeight_g": WholePlantWeight_g,
            "HeadWeight_g": HeadWeight_g,
            "HeadNumber_No": HeadNumber_No,
            "StoverWeight_g": StoverWeight_g}

        errors, warnings, weight_difference = (
            fx.validate_partitioning_measurements(WholePlantWeight_g, HeadWeight_g, HeadNumber_No, StoverWeight_g,WEIGHT_TOLERANCE)
            )

        if fx.sample_has_data(
            dataAll, row_index, TRAIT_NAMES):

            warnings.insert(0, 
                f"Partitioning data for {ID} "
                "are already on file. Continuing "
                "will overwrite the existing values."
                )

        if errors:
            st.session_state.pop("_partitioning_pending",None)

            for error in errors:
                st.error(error)

        elif warnings:
            st.session_state["_partitioning_pending"] = {"ID": ID, "values": trait_values, "warnings": warnings}

        else:
            fx.save_sample(dataAll, row_index, trait_values, filename)

            st.session_state.pop("_partitioning_pending",None)

            st.success(f"Partitioning data for {ID} "
                "were saved successfully."
                )

            st.button(
                "NEXT SAMPLE",
                on_click=fx.reset_partitioning_sample
                )

    # Confirmation
    pending = st.session_state.get("_partitioning_pending")

    if (pending is not None and pending["ID"] == ID):

        for warning in pending["warnings"]:
            st.warning(warning, icon="⚠️")

        st.caption(
            "Correct the values and click LOAD DATAPOINT "
            "again, or continue to save these values."
            )

        if st.button(
            "CONTINUE AND SAVE",
            key="confirm_partitioning_save"):

            fx.save_sample(dataAll, row_index, pending["values"], filename)

            st.session_state.pop("_partitioning_pending", None)

            st.success(
                f"Partitioning data for {ID} "
                "were saved successfully."
                )

            st.button("NEXT SAMPLE", on_click=fx.reset_partitioning_sample, key="next_sample_after_confirmation")

    with st.expander("View complete trial dataset"):

        st.dataframe(dataAll, use_container_width=True,hide_index=True)