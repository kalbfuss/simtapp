import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

df = pd.DataFrame([
    {"orgHierarchy": "A", "jobTitle": "CEO", "employmentType": "Permanent"},
    {"orgHierarchy": "A/B", "jobTitle": "VP", "employmentType": "Permanent"},
    {"orgHierarchy": "A/B/C", "jobTitle": "Manager", "employmentType": "Contract"}
])

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(flex=1)
gb.configure_column("jobTitle")
gb.configure_column("employmentType")

# Tree data setup
gb.configure_grid_options(
    treeData=True,
    getDataPath=JsCode("function(data) { return data.orgHierarchy.split('/'); }"),
    autoGroupColumnDef={
        "headerName": "Organisation Hierarchy",
        "minWidth": 300,
        "cellRendererParams": {"suppressCount": True}
    },
    groupDefaultExpanded=-1,
    animateRows=True
)

grid_options = gb.build()

AgGrid(
    df,
    gridOptions=grid_options,
    height=500,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True
)
