import pandas as pd
import streamlit as st
import os

def app():
    
    uploaded_file = st.file_uploader("Upload Plot Lenght Data", type=["csv", "xlsx"])
    # Check if file was uploaded
    if uploaded_file:
        if uploaded_file.type == "text/csv":
            df_pl = pd.read_csv(uploaded_file)
        else:
            df_pl = pd.read_excel(uploaded_file)
            
        #Get Plant Heigth data   
        plant_height_col = ['Plant Height (cm)_1', 'Plant Height (cm)_2','Plant Height (cm)_3' ,'Plant Height (cm)_4' ,'Plant Height (cm)_5','Plant Height (cm)_6', 
                           'Plant Height (cm)_7','Plant Height (cm)_8','Plant Height (cm)_9','Plant Height (cm)_10']
        df_pl['Plant Height (cm) Mean'] = df_pl[plant_height_col].mean(axis=1)
        df_pl['Plant Height (cm) SD'] = df_pl[plant_height_col].std(axis=1)
        
        st.dataframe(df_pl)
        
    uploaded_file_cb = st.file_uploader("Upload Combine Data", type=["csv", "xlsx"], accept_multiple_files = True)
    appended_data = []
    # Check if file was uploaded
    if uploaded_file_cb:
        for file in uploaded_file_cb:
            df_cb = pd.read_csv(file)
            # Retrieve location from filename
            filename = file.name
            Location, xx  = filename.split('-')
            # Add location
            df_cb['Location'] = Location.upper()
            # Select columns and rename
            df_cb = df_cb[['RANGE', 'ROW', 'PLOT', 'TRIAL_SHORT', 'Weight', 'Moisture', 'Test Weight', 'Location']]     
            df_cb.columns = ['RANGE', "ROW", "Plot", "Trial", "Weight", "Moisture", "Test Weight", 'Location']
            
            # Store DataFrame in list
            appended_data.append(df_cb)
        df_cb = pd.concat(appended_data)
    
        st.dataframe(df_cb)
        
    uploaded_file_trt = st.file_uploader("Upload Treatments Data", type=["csv", "xlsx"])
    # Check if file was uploaded
    if uploaded_file_trt:
        if uploaded_file_trt.type == "text/csv":
            df_trt = pd.read_csv(uploaded_file_trt).astype(str)
        else:
            df_trt = pd.read_excel(uploaded_file_trt).astype(str)
            
        st.dataframe(df_trt)

    
    std_moist = st.number_input("Target moisture (%)")
    
    if uploaded_file:
    
        trials = st.multiselect('TRIAL', df_pl['Trial'].unique())
        
    if st.button('Test'): 
            
        df_cb = df_cb.loc[(df_cb['Trial'] != "FILL") & (df_cb['Trial'] != "TBD") & (df_cb['Plot'] != "FILL")].dropna()
               
        st.dataframe(df_cb)
    
    
    if st.button('Create Yield File'): 
        
        for trial_name in trials:
            TRIAL = trial_name
            
            STD_MOIST = std_moist
           
            df_pl = df_pl[["Year", "Location", "Trial", "Plot", "Plot Length (m)", 'Plant Height (cm) Mean', 'Plant Height (cm) SD']]
            
            #Convert Location Names in Upper case strings - CHECK THIS
            df_pl['Location'] = df_pl['Location'].str.upper()
            df_trt['Location'] = df_trt['Location'].str.upper()           
            
            #Remove FILL, XXXX, and NA's
            df_cb = df_cb.loc[(df_cb['Trial'] != "FILL") & (df_cb['Trial'] != "TBD") & (df_cb['Plot'] != "FILL")]
            
            # Convert all Plot columns into same format
            # Combine
            df_cb['Plot'] = pd.to_numeric(df_cb['Plot'], errors='coerce')
            df_cb['Plot'] = df_cb['Plot'].astype('Int64')
            # Plot length and plant height
            df_pl['Plot'] = pd.to_numeric(df_pl['Plot'], errors='coerce')
            df_pl['Plot'] = df_pl['Plot'].astype('Int64')
            # Treatments
            df_trt['Plot'] = pd.to_numeric(df_trt['Plot'], errors='coerce')
            df_trt['Plot'] = df_trt['Plot'].astype('Int64')
            
           
    
            
            df1 = df_pl.merge(df_cb, on=["Plot","Trial", "Location"])
            df1.drop_duplicates(subset=["Plot","Trial", "Location"], keep='first', inplace=True, ignore_index=True)
            
            #Filter a specific trial
            df1 = df1[df1.Trial == TRIAL]
            
            #Set plot width 
            pw = 6 * 0.3048  
            df1['Plot Area'] = (pw * df1["Plot Length (m)"])        
            
            df1['W13'] = df1['Weight'] * (100 - df1['Moisture'] ) /(100 - STD_MOIST)
            df1['W0'] = df1['W13'] * (1 - STD_MOIST/100)
            
            
            df1['Yield Std Moist (kg/ha)'] = (df1['W13'] * 0.453392 ) / df1['Plot Area'] * 10000
            df1['Yield Dry Basis (kg/ha)'] = (df1['W0'] * 0.453392 ) / df1['Plot Area'] * 10000
            
            df1['Yield Std Moist (bu/ac)'] = ((df1['W13'] / 60 ) / df1['Plot Area']) * 4046.86
            df1['Yield Dry Basis (bu/ac)'] = ((df1['W0'] / 60 ) / df1['Plot Area']) * 4046.86
            
            df1["TW (lb/bu)"] = df1["Test Weight"]
            
            df2 = df_trt.merge(df1, on=["Plot","Trial", "Location"])
            df2.drop_duplicates(subset=["Plot","Trial", "Location"], keep='first', inplace=True, ignore_index=True)
         
            df_merged = df2[["Year", "Location", "Trial", "Plot", "TRT1", "TRT2", "TRT3", "Yield Std Moist (kg/ha)", 
                             "Yield Dry Basis (kg/ha)", "Yield Std Moist (bu/ac)", "Yield Dry Basis (bu/ac)", "TW (lb/bu)", 'Moisture',
                             'Plant Height (cm) Mean', 'Plant Height (cm) SD' ]]
            
            df_merged = df_merged[df_merged.Trial == TRIAL]
            
            #st.dataframe(df_merged)
            
            
            season = df_pl['Year'][1]
            year_folder = f'SEASON {season}'
            #folder_path = f'../{year_folder}/01-Data/{TRIAL}' Luiz PradellaS2
            folder_path = f'../{year_folder}/01-Data/Combine_Data'
            
            filename = f'{folder_path}/{TRIAL}_Combine_Data.csv'
            
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            # Luiz Pradella    
            if not os.path.isfile(f'{filename}'):
                df_merged.to_csv(filename, index = False)

    
