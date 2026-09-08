import os
from pathlib import Path

import cv2 as cv
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import simplekml
import streamlit as st
from pyproj import CRS

import functions as fx


BASE_DIR = Path(__file__).resolve().parent
LABELS_FILE = BASE_DIR / "metadata" / "Labels.csv"

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG")

FEEKES_OPTIONS = ["F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F10.1", "F10.5", "F11.1", "F11.2", "F11.3", "F11.4"]


def app():

    st.title("Imagery and Canopy Cover Tools")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Assign Coordinates", "Flight Path", "Rename Photos", "Crop Images", "Green Canopy Cover"])

    # ==================================================================
    # TAB 1 - ASSIGN COORDINATES
    # ==================================================================

    with tab1:

        st.subheader("Upload the field map and coordinates from the planter")

        col1, col2 = st.columns(2)

        with col1:
            mapPath = st.file_uploader("Upload Field Map", type=["csv", "xlsx"], key="coordinate_map")

        with col2:
            coordinatesPath = st.file_uploader("Upload Drill Coordinates", type=["csv"], key="coordinate_drill")

        if not LABELS_FILE.is_file():
            st.error("Labels.csv was not found in the metadata folder.")

        else:

            metadata = pd.read_csv(LABELS_FILE)
            labels = fx.explode_cc_labels(metadata)

            col1, col2 = st.columns(2)

            with col1:
                YEAR1 = st.selectbox("Year", sorted(labels["YEAR"].dropna().unique()), key="coordinates_year")

            with col2:
                location_options = sorted(labels.loc[labels["YEAR"] == YEAR1, "LOC_SHORT"].dropna().unique())
                LOCATION1 = st.selectbox("Location", location_options, key="coordinates_location")

            if mapPath is not None and coordinatesPath is not None:

                try:

                    dfMap = fx.read_map(mapPath)

                    cd = pd.read_csv(coordinatesPath)
                    cd = cd[["Name", "Longitude", "Latitude"]].dropna()

                    # Planter GPS starts range numbering at zero
                    cd["y"] = cd["Name"].str.extract(r"(\d+)")[0].astype(int) + 1

                    direction = st.selectbox("Planting Direction", ["South - North", "West - East", "North - South", "East - West"], key="planting_direction")

                    if direction == "South - North":
                        cd = cd.sort_values(["y", "Longitude"], ascending=[True, True])

                    elif direction == "West - East":
                        cd = cd.sort_values(["y", "Latitude"], ascending=[True, False])

                    elif direction == "North - South":
                        cd = cd.sort_values(["y", "Longitude"], ascending=[True, False])

                    elif direction == "East - West":
                        cd = cd.sort_values(["y", "Latitude"], ascending=[True, True])

                    cd["x"] = cd.groupby("y").cumcount() + 1
                    cd = cd.reset_index(drop=True)

                    dfCoor = cd

                    st.caption(f"Map positions: {len(dfMap)} | Coordinate positions: {len(dfCoor)}")

                    if st.button("Save Coordinates", key="save_coordinates"):

                        if len(dfMap) != len(dfCoor):
                            st.warning(f"The field map contains {len(dfMap)} plots but the coordinate file contains {len(dfCoor)} positions.")

                        try:

                            prev_year = 2000 + int(YEAR1) - 1
                            year_folder = f"SEASON {prev_year}-{YEAR1}"
                            out_filepath = BASE_DIR.parent / year_folder / "03-Canopy Cover" / LOCATION1
                            filename = out_filepath / "plotCoordinates.csv"

                            out_filepath.mkdir(parents=True, exist_ok=True)

                            df = pd.merge(dfMap, dfCoor, on=["x", "y"])

                            df["Location"] = LOCATION1
                            df["Year"] = YEAR1
                            df["Pixels to crop"] = 1300
                            df["Rotation"] = 0

                            df[["Trial", "Plot"]] = df["Plot"].astype(str).str.split("-", n=1, expand=True)

                            df["Label"] = df["Trial"].astype(str) + "-" + df["Location"].astype(str) + "-" + df["Year"].astype(str) + "-CCP-" + df["Plot"].astype(str)

                            df = df[["Location", "Trial", "Year", "Plot", "Label", "Latitude", "Longitude", "Pixels to crop", "Rotation"]]

                            df.to_csv(filename, index=False)

                            st.success(f"Coordinates saved successfully for {LOCATION1}.")
                            st.dataframe(df, use_container_width=True, hide_index=True)

                        except Exception as error:
                            st.error(f"Coordinates could not be saved: {error}")

                except Exception as error:
                    st.error(f"Coordinates could not be processed: {error}")

            else:
                st.info("Upload both the field map and drill coordinates to continue.")

    # ==================================================================
    # TAB 2 - FLIGHT PATH
    # ==================================================================

    with tab2:

        st.subheader("Generate Flight Path")

        if not LABELS_FILE.is_file():
            st.error("Labels.csv was not found in the metadata folder.")

        else:

            metadata = pd.read_csv(LABELS_FILE)
            labels = fx.explode_cc_labels(metadata)

            col1, col2 = st.columns(2)

            with col1:
                YEAR2 = st.selectbox("Year", sorted(labels["YEAR"].dropna().unique()), key="flight_year")

            with col2:
                location_options = sorted(labels.loc[labels["YEAR"] == YEAR2, "LOC_SHORT"].dropna().unique())
                LOCATION2 = st.selectbox("Location", location_options, key="flight_location")

            prev_year = 2000 + int(YEAR2) - 1
            year_folder = f"SEASON {prev_year}-{YEAR2}"
            out_filepath = BASE_DIR.parent / year_folder / "03-Canopy Cover" / LOCATION2
            filename = out_filepath / "plotCoordinates.csv"

            if not filename.is_file():
                st.info("Assign coordinates for this location before generating a flight path.")

            else:

                try:
                    data = pd.read_csv(filename)
                except TimeoutError:
                    st.error("The coordinates file could not be read because OneDrive timed out. Make sure the file is downloaded and available locally.")
                    return
                except Exception as error:
                    st.error(f"The coordinates file could not be read: {error}")
                    return

                if data.empty:
                    st.warning("The coordinates file is empty.")

                else:

                    TRIAL2 = st.selectbox("Trial", sorted(data["Trial"].dropna().unique()), key="flight_trial")

                    col1, col2 = st.columns(2)

                    with col1:
                        south = st.number_input("Center Latitude adjustment (m) North(-) South(+)", format="%f", key="flight_south")

                    with col2:
                        west = st.number_input("Center Longitude adjustment (m) East(-) West(+)", format="%f", key="flight_west")

                    if st.button("Generate KML", key="generate_kml"):

                        filtered_data = data[data["Trial"] == TRIAL2].copy()

                        if filtered_data.empty:
                            st.error(f"No coordinates were found for {TRIAL2}.")

                        else:

                            try:

                                df = filtered_data[["Plot", "Latitude", "Longitude"]].copy()
                                adj_c = fx.adjust_coordinates(df, south, west).dropna().reset_index(drop=True)
                                adj_c = adj_c.sort_values("Plot").reset_index(drop=True)

                                last_lat = adj_c.iloc[-1]["Latitude"]
                                last_long = adj_c.iloc[-1]["Longitude"]

                                new_row = pd.DataFrame({"Plot": [999], "Latitude": [last_lat], "Longitude": [last_long]})
                                adj_c = pd.concat([adj_c, new_row], ignore_index=True)

                                filename_kml_csv = out_filepath / f"{TRIAL2}_kml.csv"
                                adj_c.to_csv(filename_kml_csv, index=False)

                                geo = gpd.GeoDataFrame(adj_c, geometry=gpd.points_from_xy(adj_c.Longitude, adj_c.Latitude), crs=CRS.from_epsg(4326))

                                kml = simplekml.Kml()

                                for _, row in geo.iterrows():
                                    kml.newpoint(name=str(row["Plot"]), coords=[(row["Longitude"], row["Latitude"])])

                                filename_kml = out_filepath / f"{TRIAL2}.kml"
                                kml.save(str(filename_kml))

                                st.success(f"KML saved as {filename_kml.name}")
                                st.dataframe(adj_c, use_container_width=True, hide_index=True)

                            except Exception as error:
                                st.error(f"KML could not be generated: {error}")

    # ==================================================================
    # TAB 3 - RENAME PHOTOS
    # ==================================================================

    with tab3:

        st.subheader("Rename Photos")

        if not LABELS_FILE.is_file():
            st.error("Labels.csv was not found in the metadata folder.")

        else:

            metadata = pd.read_csv(LABELS_FILE)
            labels = fx.explode_cc_labels(metadata)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                YEAR3 = st.selectbox("Year", sorted(labels["YEAR"].dropna().unique()), key="rename_year")

            with col2:
                location_options = sorted(labels.loc[labels["YEAR"] == YEAR3, "LOC_SHORT"].dropna().unique())
                LOCATION3 = st.selectbox("Location", location_options, key="rename_location")

            with col3:
                trial_options = sorted(labels.loc[(labels["YEAR"] == YEAR3) & (labels["LOC_SHORT"] == LOCATION3), "TRIAL_SHORT"].dropna().unique())
                TRIAL3 = st.selectbox("Trial", trial_options, key="rename_trial")

            with col4:
                FEEKES = st.selectbox("Feekes", FEEKES_OPTIONS, key="rename_feekes")

            data = labels[(labels["LOC_SHORT"] == LOCATION3) & (labels["TRIAL_SHORT"] == TRIAL3) & (labels["YEAR"] == YEAR3)].copy()

            # Only one row per plot
            data = data[["TRIAL_SHORT", "LOC_SHORT", "YEAR", "Plot"]].drop_duplicates()
            data["Plot"] = pd.to_numeric(data["Plot"], errors="coerce")
            data = data.dropna(subset=["Plot"]).sort_values("Plot").reset_index(drop=True)

            # Sampling name keeps phenology information
            SAMPLING = f"{FEEKES}_CC"

            data["LABEL"] = data["TRIAL_SHORT"].astype(str) + "-" + data["LOC_SHORT"].astype(str) + "-" + data["YEAR"].astype(str) + "-" + SAMPLING + "-" + data["Plot"].astype(int).astype(str)

            missingPlots = st.multiselect("Select missing plots", data["Plot"].astype(int).tolist(), key="missing_canopy_plots")

            if missingPlots:
                data = data[~data["Plot"].isin(missingPlots)].reset_index(drop=True)

            st.caption(f"{len(data)} expected photos")

            if st.button("Preview Names", key="preview_photo_names"):
                st.dataframe(data[["LOC_SHORT", "TRIAL_SHORT", "YEAR", "Plot", "LABEL"]], use_container_width=True, hide_index=True)

            photos = st.text_input("Enter folder path", key="rename_folder")

            if photos:

                photo_folder = Path(photos)

                if not photo_folder.is_dir():
                    st.error("The selected folder does not exist.")

                else:

                    image_files = sorted([file for file in photo_folder.iterdir() if file.is_file() and file.suffix.lower() in [".jpg", ".jpeg", ".png"]])

                    st.caption(f"{len(image_files)} image files found | {len(data)} expected labels")

                    if len(image_files) != len(data):
                        st.warning(f"The number of labels ({len(data)}) is not equal to the number of image files ({len(image_files)}).")

                    if st.button("Rename Photos", key="rename_photos"):

                        if len(image_files) != len(data):
                            st.error("Photos were not renamed because the number of files and labels do not match.")

                        else:

                            try:

                                labels_to_use = data["LABEL"].tolist()

                                # Preview old -> new mapping before renaming
                                rename_map = pd.DataFrame({
                                    "Original": [file.name for file in image_files],
                                    "New": [f"{label}{file.suffix.upper()}" for label, file in zip(labels_to_use, image_files)]
                                })

                                st.dataframe(rename_map, use_container_width=True, hide_index=True)

                                for file, label in zip(image_files, labels_to_use):
                                    new_file = photo_folder / f"{label}{file.suffix.upper()}"

                                    if new_file.exists() and new_file != file:
                                        raise FileExistsError(f"{new_file.name} already exists.")

                                    file.rename(new_file)

                                st.success(f"{len(image_files)} photos were renamed successfully.")

                            except Exception as error:
                                st.error(f"Photos could not be renamed: {error}")

    # ==================================================================
    # TAB 4 - CROP IMAGES
    # ==================================================================

    with tab4:

        st.subheader("Image Cropper")

        directory_path = st.text_input("Enter directory path", key="crop_directory")

        if directory_path:

            directory = Path(directory_path)

            if not directory.is_dir():
                st.error("Invalid directory path.")

            else:

                files = sorted([file.name for file in directory.iterdir() if file.is_file() and file.suffix.lower() in [".jpg", ".jpeg", ".png"]])

                valid_files = []

                for file_name in files:

                    file_stem = Path(file_name).stem
                    parts = file_stem.split("-")

                    if len(parts) == 5 and parts[4].isdigit():
                        valid_files.append(file_name)

                if not valid_files:
                    st.warning("No correctly named plot images were found.")

                else:

                    repetitions = sorted(set(str(Path(file).stem.split("-")[4])[0] for file in valid_files))

                    col1, col2 = st.columns(2)

                    with col1:
                        selected_repetition = st.selectbox("Filter by Repetition", repetitions, key="crop_rep")

                    filtered_files = [file for file in valid_files if str(Path(file).stem.split("-")[4])[0] == selected_repetition]

                    with col2:
                        selected_file = st.selectbox("Select Image", filtered_files, key="crop_image")

                    if selected_file:

                        file_path = directory / selected_file
                        image = cv.imread(str(file_path))

                        if image is None:
                            st.error("Image could not be opened.")

                        else:

                            file_stem = Path(selected_file).stem

                            try:
                                qr = fx.parse_qr_code(file_stem)
                            except ValueError as error:
                                st.error(str(error))
                                return

                            TRIAL4 = qr["Trial"]
                            LOCATION4 = qr["Site"]
                            YEAR4 = qr["Year"]
                            PLOT4 = qr["Plot"]

                            prev_year = 2000 + int(YEAR4) - 1
                            year_folder = f"SEASON {prev_year}-{YEAR4:02d}"
                            coordinate_file = BASE_DIR.parent / year_folder / "03-Canopy Cover" / LOCATION4 / "plotCoordinates.csv"

                            if not coordinate_file.is_file():
                                st.error(f"Coordinates file was not found for {LOCATION4}.")

                            else:

                                coordinates = pd.read_csv(coordinate_file)

                                coordinates["Trial"] = coordinates["Trial"].astype(str).str.strip()
                                coordinates["Plot"] = pd.to_numeric(coordinates["Plot"], errors="coerce")

                                filtered_data = coordinates[(coordinates["Trial"] == TRIAL4) & (coordinates["Plot"] == PLOT4)].copy()

                                if len(filtered_data) == 0:
                                    st.error(f"Plot {PLOT4} was not found in plotCoordinates.csv.")

                                elif len(filtered_data) > 1:
                                    st.error(f"Plot {PLOT4} appears more than once in plotCoordinates.csv.")

                                else:

                                    row = filtered_data.iloc[0]

                                    saved_top = int(row["Pixels to crop"])
                                    saved_rotation = int(row["Rotation"])

                                    st.dataframe(filtered_data[["Location", "Trial", "Year", "Plot", "Label", "Pixels to crop", "Rotation"]], use_container_width=True, hide_index=True)

                                    col1, col2 = st.columns(2)

                                    with col1:
                                        rotation_angle = st.number_input("Rotation Angle", min_value=-180, max_value=180, value=saved_rotation, step=1, key=f"rotation_{selected_file}")

                                    with col2:
                                        top_text = st.number_input("Top pixels to crop", min_value=0, max_value=max(0, image.shape[0] - 1), value=min(saved_top, image.shape[0] - 1), step=30, key=f"top_{selected_file}")

                                    # --------------------------------------------------
                                    # Rotate image
                                    # --------------------------------------------------

                                    rows, cols = image.shape[:2]
                                    rotation_matrix = cv.getRotationMatrix2D((cols / 2, rows / 2), rotation_angle, 1)
                                    rotated_image = cv.warpAffine(image, rotation_matrix, (cols, rows))

                                    # --------------------------------------------------
                                    # Your current crop method
                                    # --------------------------------------------------

                                    try:
                                        cropped_image = fx.crop_image(rotated_image, top_text)

                                        if cropped_image.size == 0:
                                            st.error("The selected crop produced an empty image. Adjust the crop value.")

                                        else:

                                            fig, ax = plt.subplots(figsize=(10, 6))
                                            ax.imshow(cv.cvtColor(cropped_image, cv.COLOR_BGR2RGB))
                                            ax.axis("off")
                                            st.pyplot(fig)
                                            plt.close(fig)

                                    except Exception as error:
                                        st.error(f"Image could not be cropped: {error}")

                                    # --------------------------------------------------
                                    # Save parameters
                                    # --------------------------------------------------

                                    if st.button("Save Crop Parameters", key="save_crop_parameters"):

                                        coordinates.loc[(coordinates["Trial"] == TRIAL4) & (coordinates["Plot"] == PLOT4), "Pixels to crop"] = top_text
                                        coordinates.loc[(coordinates["Trial"] == TRIAL4) & (coordinates["Plot"] == PLOT4), "Rotation"] = rotation_angle

                                        coordinates.to_csv(coordinate_file, index=False)

                                        st.success(f"Crop parameters saved for {TRIAL4} - Plot {PLOT4}.")

    # ==================================================================
    # TAB 5 - GREEN CANOPY COVER
    # ==================================================================

    with tab5:

        st.subheader("Green Canopy Cover")

        st.info("Green canopy cover processing will remain here. Add the existing canopy cover calculation when ready.")