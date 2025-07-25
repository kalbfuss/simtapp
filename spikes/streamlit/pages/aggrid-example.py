import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder
import pandas as pd

# Sample DataFrame
data = {
    'Name': ['Alice', 'Bob', 'Charlie'],
    'Age': [25, 30, 35],
    'City': ['Berlin', 'Munich', 'Stuttgart']
}
df = pd.DataFrame(data)

# Create grid options
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("Name", editable=True)
gb.configure_column("Age", editable=True)
gb.configure_column("City", editable=True)
grid_options = gb.build()

# Display the editable Ag-Grid
st.title("Editable Ag-Grid Example")
grid_response = AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True, update_mode='MODEL_CHANGED')

# Get the updated data
updated_df = pd.DataFrame(grid_response['data'])

# Display the updated DataFrame
st.write("Updated DataFrame:")
st.dataframe(updated_df)
