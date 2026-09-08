import streamlit as st
import functions as fx

def app():
    st.title('Upload Lab Sample Weights')

    ID = st.text_input('SCAN QR CODE IN LABEL')
    #TRAIT = st.selectbox('Select Trait', ['CHAFF WEIGHT', 'GRAINS WEIGHT', 'BIOMASS WEIGHT'])
    filename, TRIAL, SITE, YEAR, TRAIT, PLOT = fx.directory_check(ID)
    WEIGHT = st.number_input('Insert Weight (g)')
        
    if st.button('LOAD DATAPOINT'):
        df = fx.upload_partitioning(ID, [TRAIT], [WEIGHT])
        st.dataframe(df)

 