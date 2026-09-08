import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from streamlit_multipage import MultiPage
import numpy as np
import os as os
import functions as fx
import datetime
import theme

INTRO = """
Log field operations and execution dates across trials and locations. Select the activity, crop stage, and date to append the entry directly to the trial history.
"""

def app():
    st.title('Record Field Activities')

    theme.intro(INTRO)

    data = pd.read_csv('metadata/Labels.csv')
    dfa = pd.read_csv('metadata/Activities.csv')
    pheno = ['F010', 'F020', 'F030', 'F040', 'F050' ,'F060' ,'F070' ,'F080' ,'F090' ,'F010' ,'F101' ,'F105' ,'F111' ,'F112' ,'F113' ,'F114']
    data = fx.explode_labels(data)
    #st.dataframe(data)
    #os.remove('labels.csv')
    ACTIVITY = st.selectbox('Activity', dfa['ACTIVITY_NAME'].unique(), help='Select the field operation or management activity to record.')

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        DATE = st.date_input("Date of activity", value=None, help='Select the date when the activity was performed in the field.')
    with col2:
        STAGE = st.selectbox('Crop stage', pheno, help='Select the growth stage of the crop at the time of the activity. Actual crop stage at which the activity was done. [Ref](https://bookstore.ksre.ksu.edu/pubs/MF3300.pdf)')
    with col3:
        LOCATION = st.multiselect('Location', data['LOC_SHORT'].unique(), help='Select the location where the activity took place.')
    with col4:
        TRIAL = st.multiselect('Trial', data['TRIAL_SHORT'].unique(), help='Select the trial associated with this field activity.')
    with col5:
        YEAR = st.selectbox('Year', data['YEAR'].unique(), help='Select the harvest year corresponding to the trial.')

    COMMENTS = st.text_input('Comments', help='Add notes regarding execution details, weather conditions, or issues affecting specific plots.')
            
    if YEAR:  
        prev_year = 2000 + int(YEAR) - 1
        year_folder = f'SEASON {prev_year}-{YEAR}'
        out_filepath = f'../{year_folder}/02-Labels/'
        
    if st.button('Save activity'):
        
        prev_year = 2000 + int(YEAR) - 1
        year_folder = f'SEASON {prev_year}-{YEAR}'
        folder_path = f'../{year_folder}/03-Activities'
        
        filename = f'{folder_path}/Activities_Dates.csv'
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        if not os.path.isfile(f'{filename}'): 
            df_create = pd.DataFrame(columns = ['LOCATION', 'YEAR', 'TRIAL', 'STAGE', 'ACTIVITY','DATE', 'COMMENTS'])
            df_create.to_csv(filename, index = False)
            
        df = pd.read_csv(filename)
        values_to_add = {'LOCATION':[LOCATION], 'YEAR':YEAR,'TRIAL':[TRIAL], 'STAGE':STAGE,'ACTIVITY':ACTIVITY,'DATE': DATE, 'COMMENTS':COMMENTS}
        temp1 = pd.DataFrame(values_to_add)
        temp1 = temp1.explode('LOCATION').explode('TRIAL')
        
        df = pd.concat([df, temp1])
        df.to_csv(filename, index = False)
        
        