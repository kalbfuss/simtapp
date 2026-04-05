"""
This page displays all projects in the database using streamlit-aggrid.
All code and documentation must be in English.
"""

import logging
import pandas as pd
import streamlit as st

from pandas.testing import assert_frame_equal

from plog.common import create_form, create_table
from plog.models.milestone import Milestone, MilestoneDate
from plog.controllers.milestone_controller import MilestoneController

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


# Get the SQLAlchemy session from Streamlit session state
session = st.session_state['session']
project = st.session_state['project']
controller = MilestoneController(session)


def milestones_table():
    """
    Show a a table with all milestones for the current project.
    """
    # Get all milestones for the current project from the database.
    milestones = controller.get_all(project=project)
    if not milestones:
        st.info("No Milestones found.")
        return

    # Define columns for display.
    columns = {
        'title': 'Title',
        'id': 'ID',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',
        'latest_baseline_date': 'Latest Baseline',
        'description': 'Description',
    }
    response = create_table(milestones, columns, parent_column='parent_id')

    # Get the selected row (if any).
    selected_rows = response.get('selected_rows', None)
    if selected_rows is not None:
        st.session_state['selected_row'] = selected_rows.iloc[0]


@st.dialog("Add Milestone")
def add_milestone():
    """
    Show a form to add a new milestone.
    """
    milestone = Milestone()
    milestone.project_id = project.id
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',
        'description': 'Description',
    }
    options = { 'parent_id': controller.possible_parents(milestone)}
    submitted = create_form(milestone, columns, options, button_label="Add")
    if submitted:
        milestone.project = project
        milestone.latest_baseline_date = milestone.initial_baseline_date
        controller.add(milestone)
        st.rerun()


@st.dialog("Edit Milestone")
def edit_milestone():
    """
    Show a form to edit an existing milestone.
    """
    # Get the select row from session state.
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("Please select a project to edit.")
        return
    milestone = controller.get_by_id(int(selected_row['id']))
    columns = {
        'title': 'Title',
        'parent_id': 'Parent',
        'acceptance_criteria': 'Acceptance Criteria',
        'initial_baseline_date': 'Initial Baseline',        
        'latest_baseline_date': 'Latest Baseline',
        'description': 'Description',
    }
    options = { 'parent_id': controller.possible_parents(milestone)}
    submitted = create_form(milestone, columns, options)
    if submitted:
        controller.update(milestone)
        st.rerun()


@st.dialog("Confirm Deletion")
def delete_milestone():
    """
    Delete the currently selected milestone after confirmation.
    """
    selected_row = st.session_state.get('selected_row', None)
    if selected_row is None:
        st.error("No project selected for deletion.")
        return
    # Show confirmation dialog
    st.warning(f"Are you sure you want to delete milestone '{selected_row['title']}' (ID {selected_row['id']})?")
    confirm = st.button("Yes, delete milestone", key="confirm_delete")
    cancel = st.button("Cancel", key="cancel_delete")
    if confirm:
        controller.delete_by_id(int(selected_row['id']))
        st.success("Project deleted.")
        del st.session_state['selected_row']
        st.rerun()
    elif cancel:
        st.info("Deletion cancelled.")
        st.rerun()


def load_dates(force=False):
    """
    Load milestone dates for the current project.

    :param force: If True, forces a reload of the milestone dates from the 
        database, even if they are already loaded in the session state.
    :return: A data frame containing all milestone dates for the current project.
    :rtype: pd.DataFrame
    """
    # Only load milestone dates if not yet done.
    if 'dates' in st.session_state and not force:
        return st.session_state['dates']

    # Get all milestones from the database.
    milestones = controller.get_all(project=project)
    if not milestones:
        return pd.DataFrame()

    # Prepare data for the table
    data = []
    for milestone in milestones:
        row = {
            'Milestone': milestone.title,
            'ID': milestone.id,
            'Initial Baseline': milestone.initial_baseline_date.strftime("%Y-%m-%d") if milestone.initial_baseline_date else None,
            'Latest Baseline': milestone.latest_baseline_date.strftime("%Y-%m-%d") if milestone.latest_baseline_date else None,
        }
        # Add milestone dates
        for date_entry in milestone.dates:
            row[f"{date_entry.entry_date.strftime('%Y-%m-%d')}"] = date_entry.date
        data.append(row)

    # Create a data frame for the dates table and save it in the session state.
    df = pd.DataFrame(data)
    st.session_state['dates'] = df
    st.session_state['dates_have_changed'] = False
    # Force refresh of the dates table to ensure it displays the newly loaded data
    refresh_dates_table()

    return df


def dates_table():
    """
    Show a table with all milestone dates for the current project.
    """
    # Load milestone dates if not yet done.
    df = load_dates()
    
    # Stop here if no milestone dates are found.
    if df.empty:
        st.info("No milestone dates found.")
        return

    # Build column configuration
    column_config = {
        'Milestone': st.column_config.TextColumn('Milestone', disabled=True),
        'ID': st.column_config.NumberColumn('ID', disabled=True),
        'Initial Baseline': st.column_config.DateColumn(
            'Initial Baseline',
            format='YYYY-MM-DD',
            disabled=True
        ),
        'Latest Baseline': st.column_config.DateColumn(
            'Latest Baseline',
            format='YYYY-MM-DD',
            disabled=True
        ),
    }
    
    # Add DateColumn config for all remaining columns
    for col in df.columns:
        if col not in column_config:
            column_config[col] = st.column_config.DateColumn(
                col,
                format='YYYY-MM-DD'
            )

    # Use st.data_editor to display and edit the table
    edited_df = st.data_editor(
        df,
        width='stretch',
        key=f"date_table_{st.session_state['dates_table_counter']}",
        hide_index=True,
        on_change=lambda: setattr(st.session_state, 'dates_have_changed', True),
        column_config=column_config,
    )
    
    return edited_df


def refresh_dates_table():
    """Force a refresh of the dates table by reloading the data and updating 
    the session state.
    """
    # Initialize table counter if not yet in session state
    if not 'dates_table_counter' in st.session_state:
        st.session_state['dates_table_counter'] = 0
        return

    # Attempt to delete current session state
    key=f"date_table_{st.session_state['dates_table_counter']}"
    if key in st.session_state:
        del st.session_state[key]

    # Update the session state
    st.session_state['dates_table_counter'] += 1
    st.session_state['dates_have_changed'] = True


@st.dialog("Add Date Column")
def dates_add_column():
    """
    Add a new date column to the table.
    """
    st.write("Select an entry date for the new column:")
    entry_date = st.date_input("Entry Date", value=pd.to_datetime("today").date(), format="YYYY-MM-DD")

    if st.button("Add Column"):
        # Load the current dates DataFrame
        df = load_dates()

        # Check if the column already exists
        new_column_name = entry_date.strftime("%Y-%m-%d")
        if new_column_name in df.columns:
            st.warning(f"Column '{new_column_name}' already exists. Please select a different date.")
            return

        # Add a new column with the selected entry date as the header
        df[new_column_name] = None

        # Sort date columns in ascending order
        protected_columns = ['Milestone', 'ID', 'Initial Baseline', 'Latest Baseline']
        date_columns = [col for col in df.columns if col not in protected_columns]
        date_columns_sorted = sorted(date_columns)
        
        # Reorder columns: protected columns first, then sorted date columns
        column_order = protected_columns + date_columns_sorted
        df = df[[col for col in column_order if col in df.columns]]

        # Update the session state with the new DataFrame and refresh the table
        st.session_state['dates'] = df
        refresh_dates_table()

        st.success(f"Column '{new_column_name}' added successfully!")
        st.rerun()


@st.dialog("Delete Date Column")
def dates_delete_column():
    """
    Delete an existing date column from the table.
    """
    # Load the current DataFrame
    df = load_dates()
    
    # Get all available date columns (exclude protected columns)
    protected_columns = ['Milestone', 'ID', 'Initial Baseline', 'Latest Baseline']
    available_columns = [col for col in df.columns if col not in protected_columns]
    
    # Check if there are any columns to delete
    if not available_columns:
        st.error("No date columns available to delete.")
        return
    
    # Display selection of entry dates
    st.write("Select an entry date (column) to delete:")
    selected_column = st.selectbox(
        "Entry Date",
        available_columns,
        key="delete_col_select"
    )
    
    # Show confirmation
    st.warning(f"Are you sure you want to delete the column '{selected_column}'?")
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = st.button("Yes, delete column", key="confirm_delete_col")
    with col2:
        cancel = st.button("Cancel", key="cancel_delete_col")

    if confirm:
        # Delete the column from the DataFrame
        df.drop(columns=[selected_column], inplace=True)
        
        # Update the session state with the modified DataFrame and refresh the 
        # table
        st.session_state['dates'] = df
        st.session_state['dates_have_changed'] = True
        refresh_dates_table()
        
        st.success(f"Column '{selected_column}' deleted successfully!")
        st.rerun()

    if cancel:
        st.info("Deletion cancelled.")
        st.rerun()


def dates_save_changes(df):
    # Load the original data for comparison
    original_df = load_dates()
    
    # Iterate over the rows in the DataFrame to update the milestone dates
    for _, row in df.iterrows():
        milestone_id = row['ID']
        milestone = controller.get_by_id(milestone_id)
        
        # Iterate over the columns representing dates
        for column in df.columns:
            if column not in ['Milestone', 'Description', 'ID', 'Initial Baseline', 'Latest Baseline']:
                entry_date = pd.to_datetime(column).date()
                new_date_value = pd.to_datetime(row[column]).date() if pd.notna(row[column]) else None
                
                # Get the original value for comparison
                original_row = original_df[original_df['ID'] == milestone_id].iloc[0]
                original_date_value = pd.to_datetime(original_row[column]).date() if pd.notna(original_row[column]) else None
                
                # Only update if the value has changed
                if new_date_value != original_date_value:
                    date_entry = controller.get_date_by_milestone_and_entry_date(milestone_id, entry_date)
                    if date_entry:
                        date_entry.date = new_date_value
                        controller.update_date(date_entry)
                    else:
                        new_date = MilestoneDate(
                            milestone_id=milestone_id,
                            entry_date=entry_date,
                            date=new_date_value
                        )
                        controller.add_date(new_date)
    
    st.session_state['dates_have_changed'] = False
    st.success("Changes saved successfully!")
    st.rerun()


@st.dialog("Confirm Discard Changes")
def dates_discard_changes():
    st.warning("Are you sure you want to discard all changes?")
    
    col1, col2 = st.columns(2)
    with col1:
        confirm = st.button("Yes, discard changes", key="confirm_discard")
    with col2:
        cancel = st.button("Cancel", key="cancel_discard")

    if confirm:
        load_dates(force=True)
        st.success("All changes discarded.")
        st.rerun()
    elif cancel:
        st.info("Discard cancelled.")
        st.rerun()


# Start page code.
st.set_page_config(layout="wide")
st.title("Milestones")
st.write("This page allows you to manage milestones for your current project.")

tabs = st.tabs(["Milestones", "Dates"])

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
    df = dates_table()
    if st.button("Add Column"):
        dates_add_column()
    if st.button("Delete Column"):
        dates_delete_column()
    if st.button("Save Changes", disabled=not st.session_state['dates_have_changed']):
        dates_save_changes(df)
    if st.button("Discard Changes", disabled=not st.session_state['dates_have_changed']):
        dates_discard_changes()