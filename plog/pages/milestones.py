"""
This page displays all projects in the database using streamlit-aggrid.
All code and documentation must be in English.
"""

import logging
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

from pandas.testing import assert_frame_equal

from plog.common import create_form, create_table
from plog.models.milestone import Milestone, MilestoneDate
from plog.controllers.milestone_controller import MilestoneController

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from plog.pages.milestones.milestones_tab import milestones_table, add_milestone, edit_milestone, delete_milestone
from plog.pages.milestones.dates_tab import load_dates, dates_table, dates_add_column, dates_delete_column, dates_save_changes, dates_discard_changes
from plog.pages.milestones.trend_tab import build_trend_chart


# Get the SQLAlchemy session from Streamlit session state
session = st.session_state['session']
project = st.session_state['project']
controller = MilestoneController(session)

# Centralized configuration for chart settings
CHART_CONFIG = {
    'font_size': 16,
    'title_font_size': 20,
    'axis_title_font_size': 20,
    'axis_label_font_size': 16,
    'legend_font_size': 16,
    'marker_size': 10,
    'height': 600,
}


# Start page code.
st.set_page_config(layout="wide")
st.title("Milestones")
#st.write("This page allows you to manage milestones for your current project.")

tabs = st.tabs(["Milestones", "Dates", "Trend"])

# Milestones tab
with tabs[0]:
    milestones_table()
    if st.button("Add"):
        add_milestone()
    if st.button("Edit"):
        edit_milestone()
    if st.button("Delete"):
        delete_milestone()

# Dates tab
with tabs[1]:
    result = dates_table()
#    st.session_state['dates'] = result['data']
    if st.button("Add Column"):
        dates_add_column()
    if st.button("Delete Column"):
        dates_delete_column()
    if st.button("Save Changes", disabled=not st.session_state['dates_have_changed']):
        dates_save_changes(result['data'])
    if st.button("Discard Changes", disabled=not st.session_state['dates_have_changed']):
        dates_discard_changes()

# Trend tab
with tabs[2]:
    # Milestone selection for the Trend tab
    milestones = controller.get_all(project=project)
    milestone_options = {milestone.title: milestone.id for milestone in milestones}

    selected_milestone_names = st.multiselect(
        "Select Milestones to Display",
        options=list(milestone_options.keys()),
        default=list(milestone_options.keys())
    )

    st.session_state.selected_milestone_ids = [milestone_options[name] for name in selected_milestone_names]

    # Build and display the trend chart
    fig = build_trend_chart()
    st.plotly_chart(fig, use_container_width=True)