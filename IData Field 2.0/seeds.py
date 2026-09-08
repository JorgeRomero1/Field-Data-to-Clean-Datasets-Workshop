from pathlib import Path

import os
import pandas as pd
import streamlit as st
from PIL import Image

import functions as fx
import theme


BASE_DIR = Path(__file__).resolve().parent

INTRO = """
Scan the QR code on your plot label to automatically load the correct trial, location, year, and plot number. Once loaded, enter the sample weight after removing broken grains and upload an image of the grains to calculate and record Thousand Kernel Weight (TKW).
"""


def app():

    st.title("Count Seeds and Estimate Thousand Kernel Weight (TKW)")

    theme.intro(INTRO)

    # -------------------------------------------------------------
    # QR code
    # -------------------------------------------------------------

    ID = st.text_input("Scan QR code on label")

    if not ID:
        st.info("Scan a QR code to start.")
        return

    # -------------------------------------------------------------
    # Read QR
    # -------------------------------------------------------------

    try:
        qr = fx.parse_qr_code(ID)
    except ValueError as error:
        st.error(str(error))
        return

    TRIAL = qr["Trial"]
    SITE = qr["Site"]
    YEAR = qr["Year"]
    PLOT = qr["Plot"]

    # -------------------------------------------------------------
    # Find trial file
    # -------------------------------------------------------------

    prev_year = 2000 + int(YEAR) - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"
    filename = BASE_DIR.parent / year_folder / "01-Data" / TRIAL / f"{TRIAL}_trial.csv"

    if not filename.is_file():
        st.error(f"Trial file was not found: {filename}")
        return

    # -------------------------------------------------------------
    # Load trial
    # -------------------------------------------------------------

    try:
        dataAll = pd.read_csv(filename)
        row_index = fx.find_plot(dataAll, SITE, PLOT)
    except Exception as error:
        st.error(str(error))
        return

    # -------------------------------------------------------------
    # Sample information
    # -------------------------------------------------------------

    st.markdown(f"**Trial:** {TRIAL} &nbsp;&nbsp; **Site:** {SITE} &nbsp;&nbsp; **Plot:** {PLOT}")

    # -------------------------------------------------------------
    # Check existing TKW
    # -------------------------------------------------------------

    existing_TKW = dataAll.at[row_index, "ThousandKernelWeight_g"]

    if pd.notna(existing_TKW):
        st.warning(f"TKW for {ID} is already on file ({existing_TKW:.2f} g). Saving again will overwrite the existing value.", icon="⚠️")

    # -------------------------------------------------------------
    # Grain weight and image
    # -------------------------------------------------------------

    GRAIN_WEIGHT = st.number_input("Grain sample weight (g)", min_value=0.0, step=0.01)

    image = st.file_uploader("Upload Grains Image", type=["jpg", "jpeg", "png"])

    if image:
        st.image(image)

        if GRAIN_WEIGHT > 0:
            try:
                TKW = fx.count_seeds(image, GRAIN_WEIGHT)
                st.metric("Thousand Kernel Weight", f"{TKW:.2f} g")
            except Exception as error:
                st.error(f"Error processing grains image: {error}")
                return

    # -------------------------------------------------------------
    # Check grain arrangement
    # -------------------------------------------------------------

    if st.button("Check grains arrangement"):

        if os.path.isfile("tempImage.jpg"):
            with Image.open("tempImage.jpg") as processed_image:
                st.image(processed_image)

            os.remove("tempImage.jpg")

        else:
            st.warning("Upload and process a grains image first.")

    # -------------------------------------------------------------
    # Save TKW
    # -------------------------------------------------------------

    if st.button("Load TKW data point"):

        if image is None:
            st.error("Upload a grains picture before saving.")
            return

        if GRAIN_WEIGHT <= 0:
            st.error("Grain sample weight must be greater than 0.")
            return

        try:
            TKW = fx.count_seeds(image, GRAIN_WEIGHT)
        except Exception as error:
            st.error(f"Error processing grains image: {error}")
            return

        if pd.notna(existing_TKW):
            st.session_state["_tkw_pending"] = {"ID": ID, "TKW": TKW}
        else:
            dataAll.at[row_index, "ThousandKernelWeight_g"] = TKW
            fx.save_csv(dataAll, filename)
            st.success(f"TKW for {ID} saved successfully.")

    # -------------------------------------------------------------
    # Confirm overwrite
    # -------------------------------------------------------------

    pending = st.session_state.get("_tkw_pending")

    if pending is not None and pending["ID"] == ID:

        st.warning("Existing Thousand Kernel Weight will be overwritten.", icon="⚠️")

        if st.button("CONTINUE AND SAVE"):
            dataAll.at[row_index, "ThousandKernelWeight_g"] = pending["TKW"]
            fx.save_csv(dataAll, filename)
            st.session_state.pop("_tkw_pending", None)
            st.success(f"TKW for {ID} saved successfully.")

    # -------------------------------------------------------------
    # Current plot
    # -------------------------------------------------------------

    with st.expander("View current plot data"):
        st.dataframe(dataAll.loc[[row_index], ["Trial", "Site", "Year", "Plot", "ThousandKernelWeight_g"]], use_container_width=True, hide_index=True)