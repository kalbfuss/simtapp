import streamlit as st
from streamlit_tree_independent_components import tree_independent_components

# Define the tree structure
treeItems = {
    "id": "0",
    "name": "Project Dashboard",
    "disable": False,
    "children": [
        {
            "id": "1",
            "name": "Technology Expense Summary",
            "disable": False,
            "children": [
                {
                    "id": "2",
                    "name": "Cost Efficiency Analysis",
                    "disable": False,
                    "children": [
                        {"id": "3", "name": "Financial Data Preparation", "disable": False},
                        {"id": "4", "name": "Database Operations Review", "disable": False}
                    ]
                }
            ]
        }
    ]
}

# Pre-selected items
checkItems = ["0", "1", "2"]

# Render the tree component
result = tree_independent_components(
    treeItems,
    checkItems=checkItems,
    disable=False,
    single_mode=False,
    show_select_mode=True,
    x_scroll=True,
    y_scroll=True,
    x_scroll_width=40,
    frameHeight=20,
    border=True
)

# Display the result
st.write("Selected node IDs:", result.get("setSelected", []))
