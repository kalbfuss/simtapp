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


def get_colors(count):
    """
    Generate a list of distinct colors for data visualization.

    :param count: The number of distinct colors to generate.
    :return: A list of color hex strings.
    :rtype: list
    """
    # Use a set of distinct colors from a predefined palette
    color_palette = [
        '#1f77b4',  # blue
        '#ff7f0e',  # orange
        '#2ca02c',  # green
        '#d62728',  # red
        '#9467bd',  # purple
        '#8c564b',  # brown
        '#e377c2',  # pink
        '#7f7f7f',  # gray
        '#bcbd22',  # olive
        '#17becf',  # cyan
        '#aec7e8',  # light blue
        '#ffbb78',  # light orange
        '#98df8a',  # light green
        '#ff9896',  # light red
        '#c5b0d5',  # light purple
    ]
    
    # Repeat the palette if more colors are needed
    if count <= len(color_palette):
        return color_palette[:count]
    
    # For more than 15 colors, cycle through the palette
    colors = []
    for i in range(count):
        colors.append(color_palette[i % len(color_palette)])
    return colors


def get_line_styles(count):
    """
    Generate a list of distinct line styles for data visualization.

    :param count: The number of distinct line styles to generate.
    :return: A list of line style strings.
    :rtype: list
    """
    # Use a set of distinct line styles
    line_styles = [
        'solid',
        'dash',
        'dot',
        'dashdot',
        'longdash',
        'longdashdot',
    ]
    
    # Repeat the line styles if more styles are needed
    if count <= len(line_styles):
        return line_styles[:count]
    
    # For more than 6 line styles, cycle through the styles
    styles = []
    for i in range(count):
        styles.append(line_styles[i % len(line_styles)])
    return styles


def get_symbols(count):
    """
    Generate a list of distinct symbols for data visualization.

    :param count: The number of distinct symbols to generate.
    :return: A list of symbol strings.
    :rtype: list
    """
    # Use a set of distinct symbols
    symbols = [
        'circle',
        'square',
        'diamond',
        'cross',
        'x',
        'triangle-up',
        'triangle-down',
        'pentagon',
        'hexagon',
        'octagon',
        'star',
        'star-diamond',
        'star-triangle-up',
        'star-triangle-down',
        'star-square',
    ]
    
    # Repeat the symbols if more symbols are needed
    if count <= len(symbols):
        return symbols[:count]
    
    # For more than 15 symbols, cycle through the symbols
    symbol_list = []
    for i in range(count):
        symbol_list.append(symbols[i % len(symbols)])
    return symbol_list


def prepare_trend_data():
    """
    Transform the milestone dates DataFrame into trace-ready format for Plotly.

    Extracts milestone names, entry dates, and target dates from the session state
    DataFrame to prepare data for visualization.
    
    :return: A dictionary mapping milestone_id to milestone data including name
        and x/y coordinates for the trend line.
    :rtype: dict
    """
    df = st.session_state.get('dates', pd.DataFrame())
    
    if df.empty:
        return {}
    
    # Define protected columns that should not be used as entry dates
    protected_columns = ['Milestone', 'ID', 'Initial Baseline', 'Latest Baseline']
    
    # Extract entry dates from column names (x-axis values)
    entry_dates = [col for col in df.columns if col not in protected_columns]
    entry_dates_sorted = sorted(entry_dates)
    
    # Convert entry dates from strings to datetime objects
    entry_dates_dt = [pd.to_datetime(d).date() for d in entry_dates_sorted]
    
    # Build trace data for each milestone
    trace_data = {}
    for _, row in df.iterrows():
        milestone_id = int(row['ID'])
        milestone_name = row['Milestone']
        
        # Skip if milestone is not selected
        if 'selected_milestone_ids' in st.session_state and milestone_id not in st.session_state.selected_milestone_ids:
            continue
        
        # Collect target dates for this milestone across all entry dates
        target_dates = []
        for entry_date in entry_dates_sorted:
            value = row[entry_date]
            if pd.notna(value):
                target_dates.append(pd.to_datetime(value).date())
            else:
                target_dates.append(None)
        
        trace_data[milestone_id] = {
            'name': milestone_name,
            'x': entry_dates_dt,
            'y': target_dates,
        }
    
    return trace_data


def build_trend_chart():
    """
    Build a Plotly figure displaying milestone target date trends.

    Creates an XY line chart with one line per milestone showing how target dates
    evolve over time (entry dates). Includes a diagonal reference line and shaded
    area below it to indicate the physically impossible region.
    
    :return: A Plotly Figure object with all traces and layout configured.
    :rtype: plotly.graph_objects.Figure
    """
    trace_data = prepare_trend_data()
    
    # Initialize figure
    fig = go.Figure()
    
    # Determine the date range for the reference line
    all_dates = []
    for milestone in trace_data.values():
        all_dates.extend(milestone['x'])
    
    if not all_dates:
        # Return empty figure if no data
        fig.add_annotation(
            text="No milestone date data available.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14)
        )
        return fig
    
    min_date = min(all_dates)
    max_date = max(all_dates)
    
    # Ensure range includes both axes properly
    for milestone in trace_data.values():
        all_dates.extend(milestone['y'])
    
    min_date_all = min([d for d in all_dates if d is not None])
    max_date_all = max([d for d in all_dates if d is not None])
    
    # Extend range slightly to accommodate the reference line
    date_range_start = min(min_date, min_date_all)
    date_range_end = max(max_date, max_date_all)
    
    # Extend the range slightly beyond the data range (+/-5%)
    from datetime import timedelta
    date_range_duration = date_range_end - date_range_start
    date_range_start = date_range_start - timedelta(days=date_range_duration.days * 0.05)
    date_range_end = date_range_end + timedelta(days=date_range_duration.days * 0.05)
    
    # Add diagonal reference line (no change: entry_date = target_date)
    fig.add_trace(go.Scatter(
        x=[date_range_start, date_range_end],
        y=[date_range_start, date_range_end],
        mode='lines',
        line=dict(color='rgba(200, 200, 200, 0.8)', width=2, dash='dash'),
        hovertemplate='<b>No change</b><br>Entry Date: %{x|%Y-%m-%d}<br>Target Date: %{y|%Y-%m-%d}<extra></extra>',
        showlegend=False,
    ))
    
    # Add gray fill area below the diagonal
    fig.add_trace(go.Scatter(
        x=[date_range_start, date_range_end, date_range_start, date_range_start],
        y=[date_range_start, date_range_end, date_range_end, date_range_start],
        fill='toself',
        fillcolor='rgba(220, 220, 220, 0.3)',
        line=dict(color='rgba(0, 0, 0, 0)'),
        hoverinfo='skip',
        showlegend=False,
        name='Impossible region',
    ))
    
    # Get colors, line styles, and symbols for all milestones
    num_milestones = len(trace_data)
    colors = get_colors(num_milestones)
    line_styles = get_line_styles(num_milestones)
    symbols = get_symbols(num_milestones)
    
    # Add a trace for each milestone
    for idx, (milestone_id, data) in enumerate(sorted(trace_data.items())):
        # Filter out None values for plotting
        valid_data = [(x, y) for x, y in zip(data['x'], data['y']) if y is not None]
        
        if not valid_data:
            continue
        
        x_vals, y_vals = zip(*valid_data)
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines+markers',
            name=data['name'],
            line=dict(color=colors[idx], width=2, dash=line_styles[idx]),
            marker=dict(size=CHART_CONFIG['marker_size'], symbol=symbols[idx], color=colors[idx]),
            hovertemplate='<b>%{fullData.name}</b><br>Entry Date: %{x|%Y-%m-%d}<br>Target Date: %{y|%Y-%m-%d}<extra></extra>',
        ))
    
    # Update layout
    fig.update_layout(
        xaxis_title='Entry Date',
        yaxis_title='Target Date',
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d',
            title_font_size=CHART_CONFIG['axis_title_font_size'],
            tickfont=dict(size=CHART_CONFIG['axis_label_font_size']),
            range=[date_range_start, date_range_end],
        ),
        yaxis=dict(
            type='date',
            tickformat='%Y-%m-%d',
            title_font_size=CHART_CONFIG['axis_title_font_size'],
            tickfont=dict(size=CHART_CONFIG['axis_label_font_size']),
            range=[date_range_start, date_range_end],
        ),
        hovermode='x unified',
        dragmode='zoom',
        legend=dict(
            x=1.02,
            y=1,
            xanchor='left',
            yanchor='top',
            bgcolor='rgba(255, 255, 255, 0.95)',
            bordercolor='rgba(0, 0, 0, 0.2)',
            borderwidth=1,
            font_size=CHART_CONFIG['legend_font_size'],
        ),
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        margin=dict(l=80, r=220, t=40, b=80),
        height=CHART_CONFIG['height'],
        font=dict(size=CHART_CONFIG['font_size']),
    )
    
    return fig


# Start page code.
st.set_page_config(layout="wide")
st.title("Milestones")
st.write("This page allows you to manage milestones for your current project.")

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
    df = dates_table()
    if st.button("Add Column"):
        dates_add_column()
    if st.button("Delete Column"):
        dates_delete_column()
    if st.button("Save Changes", disabled=not st.session_state['dates_have_changed']):
        dates_save_changes(df)
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