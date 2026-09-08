import streamlit as st
import functions as fx
import os
import pandas as pd


def app():    
    ID = st.text_input('SCAN QR CODE IN LABEL')
    
    TRAITS = ['Whole Plant Weight', 'Head Weight','Head Number', 'Stover Weight']
    
    if ID: 
        filename, TRIAL, SITE, YEAR, SAMPLING, PLOT = fx.directory_check(ID)
        
        if os.path.exists(filename):
            temp_df = pd.read_csv(filename)
            
            idx =  (temp_df['SITE'] == SITE) & (temp_df['YEAR'] == int(YEAR)) & (temp_df['TRAIT'].isin(TRAITS)) & (temp_df['PLOT'] == int(PLOT))
            temp_df2 = temp_df[idx]

            if temp_df2.shape[0] > 0:
                st.warning(f'Partitioning data for {ID} is already on file. If you continue processing the sample, it will generate a duplicate.', icon="⚠️")
  
    col1, col2, col3, col4 = st.columns(4)    
    
    with col1: 
        MASS = st.number_input(f'{TRAITS[0]} (g)')
    with col2: 
        MASS_2 = st.number_input(f'{TRAITS[1]} (g)')
    with col3:
        MASS_3 = st.number_input(f'{TRAITS[2]}')
    with col4:
        MASS_4 = st.number_input(f'{TRAITS[3]} (g)')
        
    WEIGHTS = [MASS, MASS_2, MASS_3, MASS_4]
        
    if st.button('LOAD DATAPOINT'):
        
        # Weight of the sum of stover and heads
        stoverHeads = MASS_2 + MASS_4
        wholePlant = MASS
        weightDif = abs((wholePlant - stoverHeads)/wholePlant)*100
        
        if weightDif > 2:
            st.warning('There are inconsistencies between weights uploaded. Please check input values and click Continue to upload the sample', icon="⚠️")
            if st.button('Continue'):
                df = fx.upload_partitioning(ID, TRAITS, WEIGHTS)
                st.dataframe(df)               
        else:
            df = fx.upload_partitioning(ID, TRAITS, WEIGHTS)
            st.dataframe(df)