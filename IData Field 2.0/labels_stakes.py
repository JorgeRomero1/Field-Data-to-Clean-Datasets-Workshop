#Import Libraries
import pandas as pd 
import numpy as np
#Directories management 
import os as os
import streamlit as st
import functions as fx

def app():
    st.title('Generate Stake Labels')

    metadata = 'metadata/Labels.csv'
    data = pd.read_csv(metadata)   
    df = fx.explode_plot_labels(data)
    df.to_csv("labels.csv", index = False)    

    if os.path.isfile('labels.csv'): 
        #labels = pd.read_csv('labels.csv')
        os.remove('labels.csv')

        col1, col2, col3 = st.columns(3)
        
        with col1:
            YEAR = st.multiselect('Year', df['YEAR'].unique())
        with col2:
            options = df[df['YEAR'].isin(YEAR)]['TRIAL_SHORT'].unique()
            TRIAL = st.multiselect('Trial', options)
        with col3:
            FILENAME = st.text_input('File name')

        idx = df['TRIAL_SHORT'].isin(TRIAL) & df['YEAR'].isin(YEAR)
        data = df[idx].drop_duplicates(subset=['LABEL'])
        
        
        
    if st.button('Filter labels'):
        if YEAR: 
            YEAR = YEAR[0]    
            prev_year = 2000 + int(YEAR) - 1
            year_folder = f'SEASON {prev_year}-{YEAR}'
            out_filepath = f'../{year_folder}/02-Labels/'

        if not os.path.exists(out_filepath):
            os.makedirs(out_filepath)
            
        st.dataframe(data, 
                     hide_index = True, 
                     column_order=("TRIAL_SHORT", "LOC_SHORT","YEAR","SAMPLING","Plot", "LABEL" )
                    )            
    
    uploadedTreatments = st.file_uploader("For PLOT LABELS upload treatments file", type=["csv", "xlsx"])
    # Check if file was uploaded
    if uploadedTreatments:
        if uploadedTreatments.type == "text/csv":
            dataTrt = pd.read_csv(uploadedTreatments)
        else:
            dataTrt = pd.read_excel(uploadedTreatments)
        ## Rename treatments file
        dataTrt.columns = ['LOC_SHORT', 'TRIAL_SHORT', 'TRT1', 'TRT2', 'TRT3', 'Plot']
        st.dataframe(dataTrt.head())
    
    if st.button('Download plot labels'):
        data = data[['Plot', 'TRIAL_SHORT', 'LOC_SHORT', 'YEAR']]
        
        # Merge data with treatments data
        outPs = data.merge(dataTrt, on=["Plot","TRIAL_SHORT", "LOC_SHORT"]) 
        
        outPs = outPs.transpose()
        outPs.to_excel(f"{FILENAME}.xlsx", index=False)
        st.dataframe(outPs)
    
