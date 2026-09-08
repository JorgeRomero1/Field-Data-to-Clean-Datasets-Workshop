import pandas as pd 
import numpy as np
import os as os
import streamlit as st
import functions as fx
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import math
import plotly.graph_objects as go

def app():
    if os.path.isfile('metadata/Labels.csv'):
        data = pd.read_csv('metadata/Labels.csv') # Specify the sheet that is reading
        data = fx.explode_labels(data)
        # Read Traits
        #traits = pd.read_csv('metadata/Traits.csv') 
    col1, col2, col3 = st.columns(3)
    with col1:
        TRIAL = st.selectbox('Trial', data['TRIAL_SHORT'].unique())
        #
    
    with col2:
        options = data[data['TRIAL_SHORT'].isin([TRIAL])]['YEAR'].unique()
        YEAR = st.multiselect('Harvest Year', options)

    if YEAR:
        df_list = []
        for i in YEAR:
            prev_year = 2000 + int(i) - 1
            year_folder = f'SEASON {prev_year}-{i}'
            out_filepath = f'../{year_folder}/01-Data/{TRIAL}/'
            filename = f'{out_filepath}/{TRIAL}.csv'
            tem_df = pd.read_csv(filename, index_col=None)
            df_list.append(tem_df)
        df = pd.concat(df_list, ignore_index=True)
        
            
        st.dataframe(df)

        #boxplots
        #allowed X columns
        allowed_x_cols = ['YEAR', 'LOC_SHORT', 'TRT1', 'TRT2', 'TRT3']
        x_options = [col for col in allowed_x_cols if col in df.columns and df[col].notna().any()]

        #define x and y
        left, right = st.columns(2)
        x_col = left.selectbox("Select X:", x_options)
        y_all_options = [col for col in df.columns if col != x_col]
        y_cols = right.multiselect("Select Y:", y_all_options, default=y_all_options[:1]) 
        
        # Facet options
        facet_options = ["None"] + [col for col in x_options if col not in [x_col] + y_cols] #options not in x or y
        split_col = st.selectbox("Compare between:", facet_options)
        
        def plot_dual_y_box(df, x, y1, y2=None, title=None, show_legend=True, y1_range=None, y2_range=None):
            fig = go.Figure()
        
            fig.add_trace(go.Box(
                x=df[x],
                y=df[y1],
                name=y1,
                marker_color='blue',
                yaxis='y1',
                boxpoints='outliers',
                showlegend=show_legend
            ))
        
            if y2:
                fig.add_trace(go.Box(
                    x=df[x],
                    y=df[y2],
                    name=y2,
                    marker_color='red',
                    yaxis='y2',
                    boxpoints='outliers',
                    showlegend=show_legend
                ))
        
            layout = {
                "yaxis": dict(
                    title=y1,
                    side='left',
                    range=y1_range  
                ),
                "boxmode": "group",
                "legend": dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.25,
                    xanchor="center",
                    x=0.5
                ),
                "margin": dict(b=100)
            }
            #if selected 2 y-axis variables
            if y2:
                layout["yaxis2"] = dict(
                    title=y2,
                    overlaying='y',
                    side='right',
                    range=y2_range  
                )
        
            if title:
                layout["title"] = title
        
            fig.update_layout(layout)
            return fig

        
        # plotting
        if len(y_cols) == 0:
            st.warning("Please select at least one Y variable.")
        elif len(y_cols) > 2:
            st.warning("Select no more than 2 Y variables.")
        else:
            y1 = y_cols[0]
            y2 = y_cols[1] if len(y_cols) == 2 else None
        
            if split_col == "None":
                fig = plot_dual_y_box(df, x_col, y1, y2, title=None, show_legend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                levels = sorted(df[split_col].dropna().unique())
            
                def chunks(lst, n):
                    for i in range(0, len(lst), n):
                        yield lst[i:i + n]
            
                #standard axis ranges
                y1_range = [df[y1].min(), df[y1].max()]
                y2_range = [df[y2].min(), df[y2].max()] if y2 else None

                #3 plots across, max
                for group_idx, group in enumerate(chunks(levels, 3)):
                    cols = st.columns(len(group))
                    for i, level in enumerate(group):
                        subset = df[df[split_col] == level]
                        show_legend = group_idx == 0 and i == 0
                        title = f"{split_col}: {level}"
                        fig = plot_dual_y_box(
                            subset, x_col, y1, y2,
                            title=title,
                            show_legend=show_legend,
                            y1_range=y1_range,
                            y2_range=y2_range
                        )
                        cols[i].plotly_chart(fig, use_container_width=True)
