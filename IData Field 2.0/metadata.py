from pathlib import Path

import pandas as pd
import streamlit as st

import functions as fx
import theme


BASE_DIR = Path(__file__).resolve().parent
METADATA_DIR = BASE_DIR / "metadata"

PHENO_OPTIONS = ["F010", "F020", "F030", "F040", "F050", "F060", "F070", "F080", "F090", "F101", "F105", "F111", "F112", "F113", "F114"]

INTRO = """
This section is where you set up the information required for data collection
and processing. Here, you define the trials, locations, traits, activities, and
experimental design used throughout the app. Every other tool uses the
information created here. The order matters: create trial and location first, then the experimental
design, followed by any additional sampling.
"""

PANEL_HELP = {
    "New trial": "Create a trial by entering its full name and a short name (maximum 5 alphanumeric characters). The short name is used in QR labels.",
    "New location": "Create a location by entering its full name and a short code (maximum 5 characters). The short code is used in QR labels.",
    "New activity": "Create a field operation, such as fertilization or spraying. Enter a description of up to 20 characters and a short code of up to 5 characters.",
    "Experimental design": "Create the design for a trial by selecting the trial, one or more locations, the harvest year, treatments, and replicates. This creates an empty template with one row per plot and predefined columns for the standard information collected every year.",
    "Add additional trait": "Create a variable to be measured by entering its full name and a 3-character code (e.g., Biomass sampling → BS). The code is used in QR labels.",
    "Add additional sampling": "Add sampling to an existing design by selecting the year, trial, and location, then combining the crop stage and trait (e.g., F114_BS). Each combination becomes a column in a new template, ready for data collection.",
}


def panel_help(panel):
    """Show the panel description under its title."""
    st.caption(PANEL_HELP[panel])


def app():
    st.title("Manage Trial Metadata")

    theme.intro(INTRO)

    # ------------------------------------------------------------------
    # NEW TRIAL
    # ------------------------------------------------------------------

    with st.expander("New trial"):

        panel_help("New trial")

        TRIAL_LONG = st.text_input("Insert the full name of the trial", key="trial_long")
        TRIAL_SHORT = st.text_input("Insert short name of the trial", help="Maximum number of characters is 5.", key="trial_short", max_chars=5)

        if st.button(f"Load {TRIAL_SHORT}", key="b1"):

            if not TRIAL_LONG.strip() or not TRIAL_SHORT.strip():
                st.error("Complete the trial name and short name.")

            elif not TRIAL_SHORT.isalnum():
                st.error("Trial short name can contain only letters and numbers.")

            else:
                try:
                    fx.add_metatrials(TRIAL_LONG, TRIAL_SHORT)
                    st.success(f"{TRIAL_SHORT} loaded successfully!")
                except Exception as error:
                    st.error(str(error))


    # ------------------------------------------------------------------
    # NEW LOCATION
    # ------------------------------------------------------------------

    with st.expander("New location"):

        panel_help("New location")

        LOCATION = st.text_input("Insert the full name of the location", key="location_long")
        LOC_SHORT = st.text_input("Insert short name of the location", help="Maximum number of characters is 5.", key="location_short", max_chars=5)

        if st.button(f"Load {LOC_SHORT}", key="b2"):

            if not LOCATION.strip() or not LOC_SHORT.strip():
                st.error("Complete the location name and short name.")

            elif not LOC_SHORT.isalnum():
                st.error("Location short name can contain only letters and numbers.")

            else:
                try:
                    fx.add_metalocations(LOCATION, LOC_SHORT)
                    st.success(f"{LOC_SHORT} loaded successfully!")
                except Exception as error:
                    st.error(str(error))


    # ------------------------------------------------------------------
    # NEW ACTIVITY
    # ------------------------------------------------------------------

    with st.expander("New activity"):

        panel_help("New activity")

        ACTIVITY = st.text_input("Describe the activity", key="activity_long", max_chars=20)
        ACTIVITY_SHORT = st.text_input("Insert short name for the activity", key="activity_short", max_chars=5)

        if st.button(f"Load {ACTIVITY}", key="b4"):

            if not ACTIVITY.strip() or not ACTIVITY_SHORT.strip():
                st.error("Complete the activity name and short name.")

            else:
                try:
                    fx.add_metactivity(ACTIVITY, ACTIVITY_SHORT)
                    st.success(f"{ACTIVITY_SHORT} loaded successfully!")
                except Exception as error:
                    st.error(str(error))


    # ------------------------------------------------------------------
    # LOAD METADATA
    # ------------------------------------------------------------------

    trials_file = METADATA_DIR / "Trials.csv"
    locations_file = METADATA_DIR / "Locations.csv"
    traits_file = METADATA_DIR / "Traits.csv"
    designs_file = METADATA_DIR / "Designs.csv"

    if not trials_file.is_file() or not locations_file.is_file():
        st.warning("Create trials and locations before defining an experimental design.")
        return

    trials = pd.read_csv(trials_file)
    locations = pd.read_csv(locations_file)


    # ------------------------------------------------------------------
# EXPERIMENTAL DESIGN
# ------------------------------------------------------------------

    with st.expander("Experimental design"):

        panel_help("Experimental design")

        col1, col2, col3 = st.columns(3)

        with col1:
            TRIAL = st.selectbox("Trial", sorted(trials["TRIAL_SHORT"].dropna().unique()), key="design_trial")

        with col2:
            LOCATIONS = st.multiselect("Location", sorted(locations["LOC_SHORT"].dropna().unique()), key="design_location")

        with col3:
            HARVEST_YEAR = st.number_input("Harvest year of the trial", min_value=2010, max_value=2099, value=2026, step=1, key="design_year")
            YEAR = int(HARVEST_YEAR - 2000)

        col4, col5 = st.columns(2)

        with col4:
            TRT = st.number_input("Number of treatments", min_value=1, step=1, key="design_trt")

        with col5:
            REPS = st.number_input("Number of replicates", min_value=1, step=1, key="design_reps")

        if LOCATIONS:
            st.caption(f"{len(LOCATIONS)} location(s) selected: {', '.join(LOCATIONS)}")

        if st.button(f"Load {TRIAL}", key="b5"):

            if not LOCATIONS:
                st.error("Select at least one location.")

            else:

                try:

                    for LOCATION in LOCATIONS:

                        design_status = fx.add_experimental_design(TRIAL, LOCATION, YEAR, TRT, REPS, TRIAL_CODE=9999)
                        trial_data, filename, file_status = fx.create_or_update_trial_file(TRIAL, LOCATION, YEAR, TRT, REPS, BASE_DIR)

                        if file_status == "created":
                            st.success(f"{TRIAL} created successfully with location {LOCATION}.")

                        elif file_status == "location_added":
                            st.success(f"{LOCATION} added successfully to {TRIAL}.")

                        elif file_status == "exists":
                            st.warning(f"{TRIAL} already contains {LOCATION}. No duplicate plots were added.")

                    st.caption(f"Experiment file: {filename}")

                except Exception as error:
                    st.error(str(error))


    # ------------------------------------------------------------------
    # ADD ADDITIONAL TRAIT
    # ------------------------------------------------------------------

    with st.expander("Add additional trait"):

        panel_help("Add additional trait")

        TRAIT = st.text_input("Enter full name of the trait", key="trait_long")
        TRAIT_SHORT = st.text_input("Insert short name of the trait", help="Maximum number of characters is 3.", key="trait_short", max_chars=3)

        if st.button(f"Load {TRAIT}", key="b3"):

            if not TRAIT.strip() or not TRAIT_SHORT.strip():
                st.error("Complete the trait name and short name.")

            else:
                try:
                    fx.add_metatraits(TRAIT, TRAIT_SHORT)
                    st.success(f"{TRAIT_SHORT} loaded successfully!")
                except Exception as error:
                    st.error(str(error))


    # ------------------------------------------------------------------
    # ADD ADDITIONAL SAMPLING
    # ------------------------------------------------------------------

    with st.expander("Add additional sampling"):

        panel_help("Add additional sampling")

        if not traits_file.is_file():
            st.info("Create a trait first.")
            return

        traits = pd.read_csv(traits_file)

        if not designs_file.is_file():
            st.info("Create an experimental design first.")
            return

        designs = pd.read_csv(designs_file)

        if designs.empty:
            st.info("Create an experimental design first.")
            return

        col1, col2, col3 = st.columns(3)

        with col1:
            YEAR_SAMPLE = st.selectbox("Year", sorted(designs["YEAR"].dropna().unique()), key="sample_year")

        with col2:
            trial_options = sorted(designs.loc[designs["YEAR"] == YEAR_SAMPLE, "TRIAL_SHORT"].dropna().unique())
            TRIAL_SAMPLE = st.selectbox("Trial", trial_options, key="sample_trial")

        with col3:
            location_options = sorted(designs.loc[(designs["YEAR"] == YEAR_SAMPLE) & (designs["TRIAL_SHORT"] == TRIAL_SAMPLE), "LOC_SHORT"].dropna().unique())
            LOCATION_SAMPLE = st.selectbox("Location", location_options, key="sample_location")


        design = designs[(designs["YEAR"] == YEAR_SAMPLE) & (designs["TRIAL_SHORT"] == TRIAL_SAMPLE) & (designs["LOC_SHORT"] == LOCATION_SAMPLE)].iloc[0]

        TRT_SAMPLE = int(design["TRT"])
        REPS_SAMPLE = int(design["REPS"])


        col4, col5, col6 = st.columns(3)

        with col4:
            PHENO = st.multiselect("Select sampling phenology", PHENO_OPTIONS, key="sample_pheno")

        with col5:
            TRAIT_SELECTION = st.multiselect("Select sampling traits", sorted(traits["TRAIT"].dropna().unique()), key="sample_traits")
            TRAIT_SHORT = traits.loc[traits["TRAIT"].isin(TRAIT_SELECTION), "TRAIT_SHORT"].tolist()

        with col6:
            combined = [f"{pheno}_{trait}" for pheno in PHENO for trait in TRAIT_SHORT]
            SAMPLING = st.multiselect("Crop stage x Trait", combined, key="sample_combined")


        if st.button(f"Add sampling for {TRIAL_SAMPLE} in {LOCATION_SAMPLE}", key="b6"):

            if not SAMPLING:
                st.error("Select at least one sampling combination.")

            else:
                try:
                    fx.add_sampling_metadata(TRIAL_SAMPLE, LOCATION_SAMPLE, YEAR_SAMPLE, TRT_SAMPLE, REPS_SAMPLE, SAMPLING)
                    sampling_data, filename = fx.create_or_update_sampling_file(TRIAL_SAMPLE, LOCATION_SAMPLE, YEAR_SAMPLE, TRT_SAMPLE, REPS_SAMPLE, SAMPLING)

                    st.success(f"Sampling for {YEAR_SAMPLE:02d} - {TRIAL_SAMPLE} - {LOCATION_SAMPLE} updated successfully.")
                    st.write(f"Added columns: {', '.join(SAMPLING)}")
                    st.caption(f"Sampling file: {filename}")

                except Exception as error:
                    st.error(str(error))