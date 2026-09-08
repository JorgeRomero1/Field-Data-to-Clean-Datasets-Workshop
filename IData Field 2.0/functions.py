def explode_labels(inData):
    
    """
    input: 
    output:
    This function is for...
    """
    import pandas as pd
    from numpy import arange
    
    inData = inData.dropna().reset_index()
    inData['SAMPLING'] = inData['SAMPLING'].str.replace(' ', '').str.split(pat = ",",  expand = False)
    inData['Trt1'] = pd.Series(dtype = 'object')
    inData['Rep1'] = pd.Series(dtype = 'object')
    
    for k,row in inData.iterrows():
        inData.at[k,'Trt1'] = arange(1,int(inData.at[k,'TRT'])+1)
        inData.at[k,'Rep1'] = arange(1,int(inData.at[k,'REPS'])+1)
            
    df = inData.explode('SAMPLING').explode('Rep1').explode('Trt1')
    df['Plot'] = df['Rep1'] * 100 + df['Trt1']
    df['LABEL'] = df['TRIAL_SHORT'].astype(str) + '-' + df['LOC_SHORT'].astype(str) + '-' + df['YEAR'].astype(str) + '-' + df['SAMPLING'].astype(str) + '-' + df['Plot'].astype(str)
    df = df.reset_index()
    #df.to_csv("labels.csv", index = False)
    return df

def label_generator(data, SIZE, FILENAME, out_filepath):
    import qrcode
    from pathlib import Path
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    if data.empty:
        raise ValueError("There are no labels to generate.")

    if "LABEL" not in data.columns:
        raise ValueError("The dataframe does not contain a LABEL column.")

    # Allow old code that still passes SIZE as a list
    if isinstance(SIZE, (list, tuple)):
        if len(SIZE) != 1:
            raise ValueError("Select only one label size.")
        SIZE = SIZE[0]

    if SIZE not in ["BIG", "SMALL"]:
        raise ValueError("Label size must be BIG or SMALL.")

    FILENAME = str(FILENAME).strip()

    if FILENAME.lower().endswith(".pdf"):
        FILENAME = FILENAME[:-4]

    if not FILENAME:
        raise ValueError("Enter a name for the PDF file.")

    if "/" in FILENAME or "\\" in FILENAME or ".." in FILENAME:
        raise ValueError("The file name contains invalid characters.")

    out_filepath = Path(out_filepath)
    out_filepath.mkdir(parents=True, exist_ok=True)
    output_file = out_filepath / f"{FILENAME}.pdf"

    if SIZE == "BIG":
        h, w = 2.4, 3.9
        y, x = -0.70 * inch, 0.67 * inch
        txt_size = 15
        y2, x2 = 9, 1.1 * inch
        qrsize = 2.2
        qrx, qry = 0.3 * inch, -0.5 * inch

    else:
        h, w = 1.4, 3.5
        y, x = -0.7 * inch, -0.3 * inch
        txt_size = 12
        y2, x2 = -0.1 * inch, 0.01 * inch
        qrsize = 1.6
        qrx, qry = 0.45 * inch, -0.9 * inch

    c = canvas.Canvas(str(output_file), pagesize=(w * inch, h * inch))

    for label in data["LABEL"].astype(str):

        c.translate(inch, inch)

        c.setFont("Helvetica", txt_size)
        c.setStrokeColorRGB(1, 1, 1)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(y, x, label)

        c.setFont("Helvetica", 15)
        c.drawString(y2, x2, "@KSU_WHEAT")

        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=qrsize, border=4)
        qr.add_data(label)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        c.drawInlineImage(img, x=qrx, y=qry, preserveAspectRatio=True)

        c.showPage()

    c.save()

    return output_file

def label_output_directory(YEAR, base_dir):
    from pathlib import Path

    YEAR = int(YEAR)
    prev_year = 2000 + YEAR - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"

    out_filepath = Path(base_dir).parent / year_folder / "02-Labels"
    out_filepath.mkdir(parents=True, exist_ok=True)

    return out_filepath

def explode_plot_labels(inData): 
    import pandas as pd
    from numpy import arange
    
    data = inData.dropna().reset_index()
    data['SAMPLING'] = data['SAMPLING'].str.replace(' ', '').str.split(pat = ",",  expand = False)
    data['Trt1'] = pd.Series(dtype = 'object')
    data['Rep1'] = pd.Series(dtype = 'object')

    for k,row in data.iterrows():
        data.at[k,'Trt1'] = arange(1,int(data.at[k,'TRT'])+1)
        data.at[k,'Rep1'] = arange(1,int(data.at[k,'REPS'])+1)

    df = data.explode('SAMPLING').explode('Rep1').explode('Trt1')
    df['Plot'] = df['Rep1']*100 + df['Trt1']
    df['LABEL'] = df['TRIAL_SHORT'].astype(str) + '-' + df['LOC_SHORT'].astype(str) + '-' + df['YEAR'].astype(str) + '-' + df['SAMPLING'].astype(str) + '-' + df['Plot'].astype(str)
    df = df.reset_index() 
    return df 

def directory_check(ID):
    import os
    
    TRIAL,SITE, YEAR, SAMPLING, PLOT = ID.split('-')
    
    prev_year = 2000 + int(YEAR) - 1
    year_folder = f'SEASON {prev_year}-{YEAR}'
    folder_path = f'../{year_folder}/01-Data/{TRIAL}'
    filename = f'{folder_path}/{TRIAL}.csv'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    tempOut = [filename, TRIAL, SITE, YEAR, SAMPLING, PLOT]
    return(tempOut)


def directory_check_combine(YEAR, TRIAL):
    import os
    
    prev_year = 2000 + int(YEAR) - 1
    year_folder = f'SEASON {prev_year}-{YEAR}'
    folder_path = f'../{year_folder}/01-Data/{TRIAL}'
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    filename = f'{folder_path}/{TRIAL}_Combine_Data.csv'
    
    return(filename)

def file_check_combine(LOCATION, filename, merged_data):
    import os
    import pandas as pd
    import streamlit as st
    
    if os.path.isfile(filename):
        temp1 = pd.read_csv(filename)
        
        if LOCATION in temp1['LOCATION'].unique():
            st.write(f'{LOCATION} already added.')
            
        if not LOCATION in temp1['LOCATION'].unique():
            tempOut = pd.concat([temp1, merged_data])
            tempOut.to_csv(filename, index = False)
        
    if not os.path.isfile(filename):
        merged_data.to_csv(filename, index = False)


    

def upload_partitioning(ID, TRAITS, WEIGHTS):
    import pandas as pd
    import os
    import functions as fx
    
    filename, TRIAL, SITE, YEAR, SAMPLING, PLOT = fx.directory_check(ID)

    if not os.path.isfile(f'{filename}'): 
        df_create = pd.DataFrame(columns = ['ID', 'TRAIT', 'VALUE', 'TRIAL','SITE', 'YEAR', 'SAMPLING', 'PLOT'])
        df_create.to_csv(filename, index = False)      

    df = pd.read_csv(filename)
    
    for i in range(len(TRAITS)):
        values_to_add = pd.DataFrame({'ID': [ID], 
                                      'TRAIT': [TRAITS[i]],
                                      'VALUE':[WEIGHTS[i]], 
                                      'TRIAL':[TRIAL], 
                                      'SITE':[SITE], 
                                      'YEAR':[YEAR], 
                                      'SAMPLING':[SAMPLING], 
                                      'PLOT':[PLOT]})
        
        df = pd.concat([df, values_to_add], ignore_index=True)
    
    df.to_csv(filename, index = False)
    df = pd.read_csv(filename)

    return df

def count_seeds(image, GRAIN_WEIGHT):
    
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg
    from skimage.color import rgb2gray, label2rgb
    from skimage.filters import threshold_otsu
    from skimage.morphology import area_opening, disk, binary_closing
    from skimage.measure import find_contours
    
    RGB = mpimg.imread(image)
    I = rgb2gray(RGB)
    # Apply Otsu's method
    global_threshold  = threshold_otsu(I)
    BW = I < global_threshold
    #Smoothing 
    #Remove small areas
    BW = area_opening(BW, area_threshold = 1000, connectivity=2)
    # CLosing operation (Connects small patches of True pixels)
    BW = binary_closing(BW, disk(5))
    contours = find_contours(BW,0)
    seed_num = len(contours)
    TKW = (GRAIN_WEIGHT/seed_num)*1000 #introduce fx for defining tkw 

    plt.imshow(BW, cmap = 'gray')
    plt.axis('off')
    for contour in contours:
        plt.plot(contour[:,1], contour[:,0], '-r', linewidth = 1)
    plt.savefig('tempImage.jpg')
    
    return TKW

## Metadata functions
def add_metatrials(TRIAL_LONG, TRIAL_SHORT):
    import os
    import pandas as pd
    
    filename = 'metadata/Trials.csv'
    if not os.path.isfile(filename): 
        df_create = pd.DataFrame(columns = ['Trial Name', 'TRIAL_SHORT', 'TRIAL_CODE'])
        df_create.to_csv(filename, index = False) 


    values_to_add = pd.DataFrame({'Trial Name': [TRIAL_LONG], # select box 
                                  'TRIAL_SHORT': [TRIAL_SHORT], #Select box - single trial
                                  'TRIAL_CODE': [999]})

    df = pd.read_csv(filename)
    dfnew = pd.concat([df, values_to_add], ignore_index=True)
    dfnew.to_csv(filename, index = False)

## Function to add new locations
def add_metalocations(LOCATION, LOC_SHORT):  
    import os
    import pandas as pd
    
    filename = 'metadata/Locations.csv'
    if not os.path.isfile(filename): 
        df_create = pd.DataFrame(columns = ['Location', 'LOC_SHORT'])
        df_create.to_csv(filename, index = False) 


    values_to_add = pd.DataFrame({'Location': [LOCATION], 
                                  'LOC_SHORT': [LOC_SHORT]})

    df = pd.read_csv(filename)
    dfnew = pd.concat([df, values_to_add], ignore_index=True)
    dfnew.to_csv(filename, index = False)
    
## Function to add new traits
def add_metatraits(TRAIT, TRAIT_SHORT):  
    import os
    import pandas as pd
    
    filename = 'metadata/Traits.csv'
    if not os.path.isfile(filename): 
        df_create = pd.DataFrame(columns = ['TRAIT', 'TRAIT_SHORT'])
        df_create.to_csv(filename, index = False) 


    values_to_add = pd.DataFrame({'TRAIT': [TRAIT], 
                                  'TRAIT_SHORT': [TRAIT_SHORT]})

    df = pd.read_csv(filename)
    dfnew = pd.concat([df, values_to_add], ignore_index=True)
    dfnew.to_csv(filename, index = False)
    
def add_metactivity(ACTIVITY, ACTIVITY_SHORT):
    import os
    import pandas as pd
    
    filename = 'metadata/Activities.csv'
    if not os.path.isfile(filename): 
        df_create = pd.DataFrame(columns = ['ACTIVITY', 'ACTIVITY_SHORT'])
        df_create.to_csv(filename, index = False) 


    values_to_add = pd.DataFrame({'ACTIVITY': [ACTIVITY], 
                                  'ACTIVITY_SHORT': [ACTIVITY_SHORT]})

    df = pd.read_csv(filename)
    dfnew = pd.concat([df, values_to_add], ignore_index=True)
    dfnew.to_csv(filename, index = False)

## Add trial within a field and sampling
def add_metalabels(TRIAL, LOCATION, YEAR, TRT, REPS, SAMPLING, TRIAL_CODE = 9999):
    import os
    import pandas as pd
    
    filename = 'metadata/Labels.csv'
    if not os.path.isfile(filename): 
        df_create = pd.DataFrame(columns = ['YEAR', 'TRIAL_SHORT','LOC_SHORT','TRT','REPS','SAMPLING','TRIAL_CODE'])
        df_create.to_csv(filename, index = False)
    
    values_to_add = pd.DataFrame({'YEAR': YEAR, # select box 
                                  'TRIAL_SHORT': TRIAL, #Select box - single trial
                                  'LOC_SHORT':LOCATION, # Multiple locations
                                  'TRT':TRT, # Number of treatments of the trial
                                  'REPS':REPS, # Number of replicates of the trial, make sure you have the same reps ax selected locations
                                  'SAMPLING':[SAMPLING], 
                                  'TRIAL_CODE':[TRIAL_CODE]})

    df = pd.read_csv(filename)
    dfnew = pd.concat([df, values_to_add], ignore_index=True)
    dfnew.to_csv(filename, index = False)
    
# Update samplings
def update_samplings(values_to_add, TRIAL_SHORT, YEAR, LOC_SHORT):
    
    import pandas as pd
    
    filename = 'metadata/Labels.csv'
    data = pd.read_csv(filename)
    # Select a trial to update sampling
    filtered = data[data['TRIAL_SHORT'].isin([TRIAL_SHORT]) & data['YEAR'].isin([YEAR]) & data['LOC_SHORT'].isin([LOC_SHORT])]['SAMPLING']
    sampling = filtered.str.replace(' ', '').str.split(pat = ",",  expand = False)
    out = []
    [out.extend(inner_list) for inner_list in sampling]
    # Out object contains updatdata sampling values 
    out += values_to_add
    # Convert list to string ans separate samplign times with a comma
    out = ', '.join(out)
    # Add updates sampling into the old dataframe
    condition = data['TRIAL_SHORT'].isin([TRIAL_SHORT]) & data['YEAR'].isin([YEAR]) & data['LOC_SHORT'].isin([LOC_SHORT])
    data.loc[condition, 'SAMPLING'] = out
    data.to_csv(filename, index = False)
    
    return(data)

def explode_cc_labels(inData):
    
    """
    input: 
    output:
    This function is for...
    """
    import pandas as pd
    from numpy import arange
    
    inData = inData.dropna().reset_index()
    inData['SAMPLING'] = inData['SAMPLING'].str.replace(' ', '').str.split(pat = ",",  expand = False)
    inData['Trt1'] = pd.Series(dtype = 'object')
    inData['Rep1'] = pd.Series(dtype = 'object')
    
    for k,row in inData.iterrows():
        inData.at[k,'Trt1'] = arange(1,int(inData.at[k,'TRT'])+1)
        inData.at[k,'Rep1'] = arange(1,int(inData.at[k,'REPS'])+1)
            
    df = inData.explode('SAMPLING').explode('Rep1').explode('Trt1')
    df['Plot'] = df['Rep1'] * 100 + df['Trt1']
    df = df[df['SAMPLING'].str.contains('CCP')].copy()
    del df['SAMPLING']
    df['SAM'] = 'CCP'
    
    df['LABEL'] = df['TRIAL_SHORT'].astype(str) + '-' + df['LOC_SHORT'].astype(str) + '-' + df['YEAR'].astype(str) + '-' + df['SAM'].astype(str) + '-' + df['Plot'].astype(str)
    df = df[['TRIAL_SHORT','LOC_SHORT','YEAR','Plot','SAM', 'LABEL']]
    df = df.reset_index()
    df = df.drop_duplicates(subset=['LABEL'])
    return df
# Adjust Coordinates 
def adjust_coordinates(df, south_adjustment, west_adjustment):
    import numpy as np
    df['Latitude'] -= south_adjustment / 111320
    df['Longitude'] -= west_adjustment / (111320 * np.cos(np.radians(df['Latitude'])))
    return df 
    
def read_map(mapPath):
    import pandas as pd 
    df = pd.read_excel(mapPath,header = None)
    nc = [str(i) for i in range(1, len(df.columns) + 1)]
    # Rename columns
    df.columns = nc
    df = df.dropna()
    df = df[::-1]
    df.reset_index(drop = True, inplace = True)
    df['y'] = df.index +1
    df = pd.melt(df,value_name = 'Plot', id_vars = ['y'], var_name = 'x')
    df['x'] = df['x'].astype(int)
    df = df.sort_values(['y', 'x'], ascending=[True, True])
    return df
# Function to crop the image
def crop_image(image, top):
    
    import matplotlib.pyplot as plt
    dimensions = image.shape
    h = dimensions[0]
    w = dimensions[1]
    bottom = top + 1680
    cropped_image = image[top:bottom, 1360:(w - 1360)]
    return cropped_image


#-----------------------
## Workshop Functions Update
#-----------------------
from pathlib import Path
import os

import numpy as np
import pandas as pd
import streamlit as st


TRAIT_NAMES = [
    "WholePlantWeight_g",
    "HeadWeight_g",
    "HeadNumber_No",
    "StoverWeight_g",
]


def parse_qr_code(ID):
    ID = ID.strip()
    parts = ID.split("-")

    if len(parts) != 5:
        raise ValueError(
            "Invalid QR code format. Expected: "
            "TRIAL-SITE-YEAR-SAMPLING-PLOT"
        )

    trial, site, year, sampling, plot = parts

    if not year.isdigit() or len(year) != 2:
        raise ValueError(
            f"Invalid year '{year}'. Expected a two-digit year."
        )

    if not plot.isdigit():
        raise ValueError(
            f"Invalid plot '{plot}'. Plot must be a number."
        )

    if not trial or not site or not sampling:
        raise ValueError(
            "The QR code contains an empty field."
        )

    return {
        "Trial": trial,
        "Site": site,
        "Year": int(year),
        "YearText": year,
        "Sampling": sampling,
        "Plot": int(plot),
    }


def directory_check_trial(qr, base_dir):
    prev_year = 2000 + qr["Year"] - 1
    year_folder = f"SEASON {prev_year}-{qr['YearText']}"

    folder_path = (
        Path(base_dir).parent
        / year_folder
        / "01-Data"
        / qr["Trial"]
    )

    folder_path.mkdir(parents=True, exist_ok=True)

    return folder_path / f"{qr['Trial']}_trial.csv"


def normalize_columns(data):
    data = data.copy()

    unnamed_columns = [
        col for col in data.columns
        if str(col).startswith("Unnamed:")
    ]

    if unnamed_columns:
        data = data.drop(columns=unnamed_columns)

    rename_options = {
        "LOC_SHORT": "Site",
        "SITE": "Site",
        "YEAR": "Year",
        "TRIAL_SHORT": "Trial",
        "TRIAL": "Trial",
        "PLOT": "Plot",
    }

    rename_dict = {
        old_name: new_name
        for old_name, new_name in rename_options.items()
        if old_name in data.columns
        and new_name not in data.columns
    }

    return data.rename(columns=rename_dict)


def validate_trial_columns(data):
    required_columns = [
        "Trial",
        "Year",
        "Site",
        "Plot",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:
        raise ValueError(
            "Trial file is missing required columns: "
            + ", ".join(missing_columns)
        )


def save_csv(data, filename):
    from pathlib import Path
    import os

    filename = Path(filename)
    filename.parent.mkdir(parents=True, exist_ok=True)

    temp_filename = filename.with_suffix(filename.suffix + ".tmp")
    data.to_csv(temp_filename, index=False)
    os.replace(temp_filename, filename)


def load_or_create_trial(
    filename,
    qr,
    labels_file,
    trait_names,
):
    filename = Path(filename)
    labels_file = Path(labels_file)

    file_exists = filename.is_file()

    if file_exists:
        data = pd.read_csv(filename)
        data = normalize_columns(data)

    else:
        if not labels_file.is_file():
            raise FileNotFoundError(
                f"Labels file not found: {labels_file}"
            )

        labels = pd.read_csv(labels_file)
        labels = explode_labels(labels)

        required_metadata_columns = [
            "YEAR",
            "LOC_SHORT",
            "Plot",
            "TRIAL_SHORT",
        ]

        missing_columns = [
            col
            for col in required_metadata_columns
            if col not in labels.columns
        ]

        if missing_columns:
            raise ValueError(
                "Labels.csv is missing required columns: "
                + ", ".join(missing_columns)
            )

        labels = labels[required_metadata_columns]

        labels = labels[
            (labels["TRIAL_SHORT"] == qr["Trial"])
            & (labels["YEAR"] == qr["Year"])
        ]

        labels = (
            labels
            .drop_duplicates()
            .reset_index(drop=True)
        )

        if labels.empty:
            raise ValueError(
                f"No metadata found for trial "
                f"{qr['Trial']} in year {qr['YearText']}."
            )

        data = labels.rename(
            columns={
                "LOC_SHORT": "Site",
                "YEAR": "Year",
                "TRIAL_SHORT": "Trial",
            }
        )

    validate_trial_columns(data)

    data["Site"] = (
        data["Site"]
        .astype(str)
        .str.strip()
    )

    data["Plot"] = pd.to_numeric(
        data["Plot"],
        errors="coerce",
    )

    for trait in trait_names:
        if trait not in data.columns:
            data[trait] = np.nan

    if not file_exists:
        save_csv(data, filename)

    return data


def find_plot(data, site, plot):
    matches = data.index[
        (data["Site"] == str(site).strip())
        & (data["Plot"] == int(plot))
    ].tolist()

    if len(matches) == 0:
        raise ValueError(
            f"Site {site}, Plot {plot} was not found."
        )

    if len(matches) > 1:
        raise ValueError(
            f"Site {site}, Plot {plot} appears "
            f"{len(matches)} times in the trial file."
        )

    return matches[0]


def sample_has_data(data, row_index, trait_names):
    existing_values = data.loc[
        row_index,
        trait_names,
    ]

    return existing_values.notna().any()


def validate_partitioning_measurements(
    whole_plant_weight,
    head_weight,
    head_number,
    stover_weight,
    tolerance=2,
):
    errors = []
    warnings = []

    if whole_plant_weight <= 0:
        errors.append(
            "Whole plant weight must be greater than 0."
        )

    if head_weight < 0:
        errors.append(
            "Head weight cannot be negative."
        )

    if stover_weight < 0:
        errors.append(
            "Stover weight cannot be negative."
        )

    if head_number < 0:
        errors.append(
            "Head number cannot be negative."
        )

    weight_difference = None

    if whole_plant_weight > 0:
        weight_difference = abs(
            (
                whole_plant_weight
                - (stover_weight + head_weight)
            )
            / whole_plant_weight
        ) * 100

        if weight_difference > tolerance:
            warnings.append(
                "Whole plant weight does not match "
                "head weight + stover weight. "
                f"The difference is {weight_difference:.1f}%."
            )

    return errors, warnings, weight_difference


def save_sample(
    data,
    row_index,
    values,
    filename,
):
    for trait, value in values.items():
        data.at[row_index, trait] = value

    save_csv(data, filename)


def reset_measurement_inputs():
    keys = [
        "WholePlantWeight_input",
        "HeadWeight_input",
        "HeadNumber_input",
        "StoverWeight_input",
        "_partitioning_pending",
    ]

    for key in keys:
        st.session_state.pop(key, None)


def reset_partitioning_sample():
    st.session_state["ID"] = ""

    reset_measurement_inputs()

    st.session_state.pop(
        "_partitioning_last_ID",
        None,
    )

TRIAL_FILE_COLUMNS = [
    "Trial",
    "Site",
    "Year",
    "Plot",
    "Treatment_1",
    "Treatment_2",
    "Treatment_3",
    "PlantHeight1_cm",
    "PlantHeight2_cm",
    "PlantHeight3_cm",
    "PlantHeight4_cm",
    "PlantHeight5_cm",
    "HeadNumber_No",
    "HeadWeight_g",
    "StoverWeight_g",
    "WholePlantWeight_g",
    "GrainWeight_g",
    "ThousandKernelWeight_g",
    "GrainProtein_%",
    "GrainProteinMoisture_%",
    "YieldDryBasis_KgHa",
    "TestWeight_KgHl",
    "Moisture_%"
]


def create_or_update_trial_file(TRIAL, LOCATION, YEAR, TRT, REPS, base_dir):
    from pathlib import Path
    import numpy as np
    import pandas as pd

    YEAR = int(YEAR)
    TRT = int(TRT)
    REPS = int(REPS)

    if TRT < 1 or REPS < 1:
        raise ValueError("Number of treatments and replicates must be greater than 0.")

    if TRT > 99:
        raise ValueError("The current plot numbering system supports a maximum of 99 treatments.")

    prev_year = 2000 + YEAR - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"
    folder_path = Path(base_dir).parent / year_folder / "01-Data" / TRIAL
    filename = folder_path / f"{TRIAL}_trial.csv"

    folder_path.mkdir(parents=True, exist_ok=True)

    plots = [rep * 100 + trt for rep in range(1, REPS + 1) for trt in range(1, TRT + 1)]

    new_data = pd.DataFrame({"Trial": TRIAL, "Site": LOCATION, "Year": YEAR, "Plot": plots})

    for column in TRIAL_FILE_COLUMNS:
        if column not in new_data.columns:
            new_data[column] = np.nan

    new_data = new_data[TRIAL_FILE_COLUMNS]

    if not filename.is_file():
        save_csv(new_data, filename)
        return new_data, filename, "created"

    data = pd.read_csv(filename)

    for column in TRIAL_FILE_COLUMNS:
        if column not in data.columns:
            data[column] = np.nan

    data = data[TRIAL_FILE_COLUMNS]

    location_exists = ((data["Site"].astype(str) == str(LOCATION)) & (data["Year"] == YEAR)).any()

    if location_exists:
        return data, filename, "exists"

    data = pd.concat([data, new_data], ignore_index=True)
    data = data.sort_values(["Site", "Plot"]).reset_index(drop=True)

    save_csv(data, filename)

    return data, filename, "location_added"


def add_experimental_design(TRIAL, LOCATION, YEAR, TRT, REPS, TRIAL_CODE=9999):
    from pathlib import Path
    import pandas as pd

    metadata_dir = Path(__file__).resolve().parent / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    designs_file = metadata_dir / "Designs.csv"
    labels_file = metadata_dir / "Labels.csv"

    YEAR = int(YEAR)
    TRT = int(TRT)
    REPS = int(REPS)

    BASE_SAMPLING = ["F114_WP", "F114_HD", "F114_ST", "F114_GR", "F114_CB"]

    # ------------------------------------------------------------------
    # Designs.csv
    # ------------------------------------------------------------------

    design_columns = ["YEAR", "TRIAL_SHORT", "LOC_SHORT", "TRT", "REPS", "TRIAL_CODE"]

    if designs_file.is_file():
        designs = pd.read_csv(designs_file)
    else:
        designs = pd.DataFrame(columns=design_columns)

    design_idx = (designs["YEAR"] == YEAR) & (designs["TRIAL_SHORT"].astype(str) == str(TRIAL)) & (designs["LOC_SHORT"].astype(str) == str(LOCATION))

    if design_idx.any():

        existing = designs.loc[design_idx].iloc[0]

        if int(existing["TRT"]) != TRT or int(existing["REPS"]) != REPS:
            raise ValueError(f"{TRIAL} - {LOCATION} already exists with a different number of treatments or replicates.")

        status = "exists"

    else:

        new_design = pd.DataFrame({
            "YEAR": [YEAR],
            "TRIAL_SHORT": [TRIAL],
            "LOC_SHORT": [LOCATION],
            "TRT": [TRT],
            "REPS": [REPS],
            "TRIAL_CODE": [TRIAL_CODE]
        })

        designs = pd.concat([designs, new_design], ignore_index=True)
        designs.to_csv(designs_file, index=False)

        status = "created"

    # ------------------------------------------------------------------
    # Labels.csv
    # ------------------------------------------------------------------

    label_columns = ["YEAR", "TRIAL_SHORT", "LOC_SHORT", "TRT", "REPS", "SAMPLING", "TRIAL_CODE"]

    if labels_file.is_file():
        labels = pd.read_csv(labels_file)
    else:
        labels = pd.DataFrame(columns=label_columns)

    label_idx = (labels["YEAR"] == YEAR) & (labels["TRIAL_SHORT"].astype(str) == str(TRIAL)) & (labels["LOC_SHORT"].astype(str) == str(LOCATION))

    if label_idx.any():

        current_sampling = labels.loc[label_idx, "SAMPLING"].iloc[0]

        if pd.isna(current_sampling):
            current_sampling = []
        else:
            current_sampling = [x.strip() for x in str(current_sampling).split(",")]

        sampling = list(dict.fromkeys(current_sampling + BASE_SAMPLING))

        labels.loc[label_idx, "SAMPLING"] = ", ".join(sampling)
        labels.loc[label_idx, "TRT"] = TRT
        labels.loc[label_idx, "REPS"] = REPS

    else:

        new_label = pd.DataFrame({
            "YEAR": [YEAR],
            "TRIAL_SHORT": [TRIAL],
            "LOC_SHORT": [LOCATION],
            "TRT": [TRT],
            "REPS": [REPS],
            "SAMPLING": [", ".join(BASE_SAMPLING)],
            "TRIAL_CODE": [TRIAL_CODE]
        })

        labels = pd.concat([labels, new_label], ignore_index=True)

    labels.to_csv(labels_file, index=False)

    return status

def add_sampling_metadata(TRIAL, LOCATION, YEAR, TRT, REPS, SAMPLING, TRIAL_CODE=9999):
    from pathlib import Path
    import pandas as pd

    metadata_dir = Path(__file__).resolve().parent / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    filename = metadata_dir / "Labels.csv"

    columns = ["YEAR", "TRIAL_SHORT", "LOC_SHORT", "TRT", "REPS", "SAMPLING", "TRIAL_CODE"]

    if filename.is_file():
        data = pd.read_csv(filename)
    else:
        data = pd.DataFrame(columns=columns)

    idx = (data["YEAR"] == int(YEAR)) & (data["TRIAL_SHORT"].astype(str) == str(TRIAL)) & (data["LOC_SHORT"].astype(str) == str(LOCATION))

    if idx.any():
        current = data.loc[idx, "SAMPLING"].iloc[0]
        current = [] if pd.isna(current) else [x.strip() for x in str(current).split(",")]
        combined = list(dict.fromkeys(current + SAMPLING))
        data.loc[idx, "SAMPLING"] = ", ".join(combined)

    else:
        new_row = pd.DataFrame({"YEAR": [int(YEAR)], "TRIAL_SHORT": [TRIAL], "LOC_SHORT": [LOCATION], "TRT": [int(TRT)], "REPS": [int(REPS)], "SAMPLING": [", ".join(SAMPLING)], "TRIAL_CODE": [TRIAL_CODE]})
        data = pd.concat([data, new_row], ignore_index=True)

    data.to_csv(filename, index=False)

    return data

def create_or_update_trial_file(TRIAL, LOCATION, YEAR, TRT, REPS, base_dir):
    from pathlib import Path
    import numpy as np
    import pandas as pd

    YEAR = int(YEAR)
    TRT = int(TRT)
    REPS = int(REPS)

    if TRT < 1 or REPS < 1:
        raise ValueError("Treatments and replicates must be greater than 0.")

    prev_year = 2000 + YEAR - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"

    folder_path = Path(base_dir).parent / year_folder / "01-Data" / TRIAL
    filename = folder_path / f"{TRIAL}_trial.csv"

    # Create folder if it does not exist
    folder_path.mkdir(parents=True, exist_ok=True)

    # Create plot numbers
    plots = [rep * 100 + trt for rep in range(1, REPS + 1) for trt in range(1, TRT + 1)]

    # Create rows for the new location
    new_data = pd.DataFrame({
        "Trial": TRIAL,
        "Site": LOCATION,
        "Year": YEAR,
        "Plot": plots
    })

    # Fixed trial structure
    trial_columns = [
        "Trial",
        "Site",
        "Year",
        "Plot",
        "Treatment_1",
        "Treatment_2",
        "Treatment_3",
        "PlantHeight1_cm",
        "PlantHeight2_cm",
        "PlantHeight3_cm",
        "PlantHeight4_cm",
        "PlantHeight5_cm",
        "HeadNumber_No",
        "HeadWeight_g",
        "StoverWeight_g",
        "WholePlantWeight_g",
        "GrainWeight_g",
        "ThousandKernelWeight_g",
        "GrainProtein_%",
        "GrainProteinMoisture_%",
        "YieldDryBasis_KgHa",
        "TestWeight_KgHl",
        "Moisture_%"
    ]

    for column in trial_columns:
        if column not in new_data.columns:
            new_data[column] = np.nan

    new_data = new_data[trial_columns]

    # -------------------------------------------------------------
    # File does not exist -> create it
    # -------------------------------------------------------------

    if not filename.is_file():
        save_csv(new_data, filename)
        return new_data, filename, "created"

    # -------------------------------------------------------------
    # File exists -> read and update it
    # -------------------------------------------------------------

    data = pd.read_csv(filename)

    # Make sure older files contain all fixed columns
    for column in trial_columns:
        if column not in data.columns:
            data[column] = np.nan

    # Check whether this location already exists
    location_data = data[(data["Site"].astype(str) == str(LOCATION)) & (data["Year"] == YEAR)]

    if not location_data.empty:

        expected_plots = TRT * REPS

        if len(location_data) != expected_plots:
            raise ValueError(f"{TRIAL} - {LOCATION} already exists with {len(location_data)} plots, but the current design specifies {expected_plots} plots.")

        return data, filename, "exists"

    # -------------------------------------------------------------
    # Existing trial, new location -> append location
    # -------------------------------------------------------------

    data = pd.concat([data, new_data], ignore_index=True)
    data = data.sort_values(["Site", "Plot"]).reset_index(drop=True)

    save_csv(data, filename)

    return data, filename, "location_added"

def get_trial_file(TRIAL, YEAR, base_dir):
    from pathlib import Path

    YEAR = int(YEAR)
    prev_year = 2000 + YEAR - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"

    filename = Path(base_dir).parent / year_folder / "01-Data" / TRIAL / f"{TRIAL}_trial.csv"

    if not filename.is_file():
        raise FileNotFoundError(f"Trial file was not found: {filename}")

    return filename


def get_trial_location(data, LOCATION):
    location_data = data[data["Site"].astype(str) == str(LOCATION)].copy()

    if location_data.empty:
        raise ValueError(f"Location {LOCATION} was not found in the trial file.")

    return location_data


def update_trial_data(data, edited, row_indices, columns):
    for column in columns:
        data.loc[row_indices, column] = edited[column].values

    return data
def get_trial_file(TRIAL, YEAR, base_dir):
    from pathlib import Path

    YEAR = int(YEAR)
    prev_year = 2000 + YEAR - 1
    year_folder = f"SEASON {prev_year}-{YEAR:02d}"
    filename = Path(base_dir).parent / year_folder / "01-Data" / TRIAL / f"{TRIAL}_trial.csv"

    if not filename.is_file():
        raise FileNotFoundError(f"Trial file was not found: {filename}")

    return filename


def update_trial_measurements(filename, edited, columns):
    import pandas as pd

    data = pd.read_csv(filename)

    for _, row in edited.iterrows():
        idx = (data["Trial"].astype(str) == str(row["Trial"])) & (data["Site"].astype(str) == str(row["Site"])) & (data["Year"] == int(row["Year"])) & (data["Plot"] == int(row["Plot"]))

        if idx.sum() != 1:
            raise ValueError(f"Could not uniquely identify {row['Site']} - Plot {row['Plot']}.")

        row_index = data.index[idx][0]
        data.loc[row_index, columns] = row[columns].values

    save_csv(data, filename)

    return data

def upload_nir_to_trial(trial_data, nir_data, filename, column_map, overwrite=False):
    data = trial_data.copy()

    updated = 0
    skipped = 0

    for _, sample in nir_data.iterrows():

        idx = (data["Site"].astype(str) == str(sample["Site"])) & (data["Year"] == int(sample["Year"])) & (data["Plot"] == int(sample["Plot"]))

        if idx.sum() != 1:
            raise ValueError(f"Could not uniquely identify {sample['Site']} - Plot {sample['Plot']}.")

        row_index = data.index[idx][0]
        trial_columns = list(column_map.values())

        existing_data = data.loc[row_index, trial_columns].notna().any()

        if existing_data and not overwrite:
            skipped += 1
            continue

        for nir_column, trial_column in column_map.items():
            data.at[row_index, trial_column] = sample[nir_column]

        updated += 1

    save_csv(data, filename)

    return updated, skipped

def upload_combine_to_trial(combine_data, filename, LOCATION, overwrite=False):
    import pandas as pd

    data = pd.read_csv(filename)

    updated = 0
    skipped = 0

    for _, sample in combine_data.iterrows():

        idx = (data["Site"].astype(str) == str(LOCATION)) & (data["Plot"] == int(sample["PLOT"]))

        if idx.sum() != 1:
            raise ValueError(f"Could not uniquely identify {LOCATION} - Plot {sample['PLOT']}.")

        row_index = data.index[idx][0]

        existing_data = data.loc[row_index, ["YieldDryBasis_KgHa", "TestWeight_KgHl", "Moisture_%"]].notna().any()

        if existing_data and not overwrite:
            skipped += 1
            continue

        data.at[row_index, "YieldDryBasis_KgHa"] = sample["Yield Dry Basis (kg/ha)"]
        data.at[row_index, "TestWeight_KgHl"] = sample["TW (kg/hL)"]
        data.at[row_index, "Moisture_%"] = sample["Moisture"]

        updated += 1

    save_csv(data, filename)

    return updated, skipped

