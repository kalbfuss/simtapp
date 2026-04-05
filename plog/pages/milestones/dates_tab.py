"""
This module contains the code related to the dates tab.
"""

import pandas as pd
from pandas.testing import assert_frame_equal
import streamlit as st
from datetime import date
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from plog.models.milestone import MilestoneDate
from plog.controllers.milestone_controller import MilestoneController


# Get the SQLAlchemy session from Streamlit session state
session = st.session_state['session']
project = st.session_state['project']
controller = MilestoneController(session)


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
            'ID': int(milestone.id),
            'Initial Baseline': milestone.initial_baseline_date,
            'Latest Baseline': milestone.latest_baseline_date,
        }
        # Add milestone dates
        for date_entry in milestone.dates:
            row[f"{date_entry.entry_date.strftime('%Y-%m-%d')}"] = date_entry.date.strftime('%Y-%m-%d')
        data.append(row)

    # Create a data frame for the dates table
    df = pd.DataFrame(data)

    # Identify date columns (excluding protected columns)
    protected_columns = ['Milestone', 'ID', 'Initial Baseline', 'Latest Baseline']
    date_columns = [col for col in df.columns if col not in protected_columns]

    # Sort date columns in ascending order
    date_columns_sorted = sorted(date_columns)

    # Reorder columns: protected columns first, then sorted date columns
    column_order = protected_columns + date_columns_sorted
    df = df[[col for col in column_order if col in df.columns]]

    # Save the sorted data frame in the session state
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

    # Configure AgGrid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(
        autoSizeStrategy={"type": "fitCellContents"},
    )
    gb.configure_pagination(enabled=True)
    gb.configure_default_column(
        editable=False,
        suppressMovable=True,
    )
    # Configure the date columns
    protected_columns = ['Milestone', 'ID', 'Initial Baseline', 'Latest Baseline']
    for col in df.columns:
        if col not in protected_columns:
            gb.configure_column(
                col,
                cellDataType='dateString',
                editable=True,
                type=['rightAligned'],
            )

    grid_options = gb.build()

    # Display the table using AgGrid
    result = AgGrid(
        df,
        key=f"date_table_{st.session_state['dates_table_counter']}",
        data_return_mode='AS_INPUT',
        gridOptions=grid_options,
        height=400,
        width='100%',
        enable_enterprise_modules=True,
        allow_unsafe_jscode=False,
   )

    # Delete column with unique id added by AgGrid prior to comparison
    df.drop(columns="::auto_unique_id::", inplace=True)
    # Compare the contents of the DataFrames and flag any changes
    if not result["data"].equals(df):
        st.session_state['dates_have_changed'] = True
    
    return result


def refresh_dates_table():
    """Force a refresh of the dates table by reloading the data and updating
    the session state.
    """
    # Initialize the dates table counter if not yet in the session state
    if not 'dates_table_counter' in st.session_state:
        st.session_state['dates_table_counter'] = 0
        return

    # Attempt to delete current session state
    key = f"date_table_{st.session_state['dates_table_counter']}"
    if key in st.session_state:
        del st.session_state[key]

    # Update the dates table counter
    st.session_state['dates_table_counter'] += 1


@st.dialog("Add Date Column")
def dates_add_column():
    """
    Add a new date column to the table.
    """
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

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
        st.session_state['dates_have_changed'] = True
        refresh_dates_table()

        st.success(f"Column '{new_column_name}' added successfully!")
        st.rerun()


@st.dialog("Delete Date Column")
def dates_delete_column():
    """
    Delete an existing date column from the table.
    """
    session = st.session_state['session']
    project = st.session_state['project']
    controller = MilestoneController(session)

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

    st.session_state['dates'] = df
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
        st.session_state['dates_have_changed'] = False
        st.success("All changes discarded.")
        st.rerun()
    elif cancel:
        st.info("Discard cancelled.")
        st.rerun()