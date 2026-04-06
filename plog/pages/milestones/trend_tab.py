"""
This module contains the code related to the trend tab.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from datetime import datetime

from plog.pages.milestones.dates_tab import PROTECTED_COLUMNS, load_dates


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
    df = load_dates()  # Load the milestone dates DataFrame from session state

    if df.empty:
        return {}

    # Extract entry dates from column names (x-axis values)
    entry_dates = [col for col in df.columns if col not in PROTECTED_COLUMNS]
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

    # Add vertical marker for "Today" if it falls within the date range
    today = datetime.today().date()
    if date_range_start <= today <= date_range_end:
        fig.add_trace(go.Scatter(
            x=[today, today],
            y=[date_range_start, date_range_end],
            mode='lines',
            line=dict(color='rgba(0, 0, 0, 0.5)', width=2, dash='dot'),
            hovertemplate='<b>Today</b><br>Date: %{x|%Y-%m-%d}<extra></extra>',
            showlegend=False,
        ))

        # Add label for the "Today" marker
        fig.add_annotation(
            x=today,
            y=date_range_end,
            xref='x',
            yref='y',
            text='Today',
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
            font=dict(size=12, color='rgba(0, 0, 0, 0.7)'),
            bgcolor='rgba(255, 255, 255, 0.7)',
            bordercolor='rgba(0, 0, 0, 0.3)',
            borderwidth=1,
            borderpad=4,
        )

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
            marker=dict(size=10, symbol=symbols[idx], color=colors[idx]),
            hovertemplate='<b>%{fullData.name}</b><br>Entry Date: %{x|%Y-%m-%d}<br>Target Date: %{y|%Y-%m-%d}<extra></extra>',
        ))

    # Update layout
    fig.update_layout(
        xaxis_title='Entry Date',
        yaxis_title='Target Date',
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d',
            title_font_size=20,
            tickfont=dict(size=16),
            range=[date_range_start, date_range_end],
        ),
        yaxis=dict(
            type='date',
            tickformat='%Y-%m-%d',
            title_font_size=20,
            tickfont=dict(size=16),
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
            font_size=16,
        ),
        plot_bgcolor='rgba(240, 240, 240, 0.5)',
        paper_bgcolor='white',
        height=600,
        font=dict(size=16),
    )

    return fig
