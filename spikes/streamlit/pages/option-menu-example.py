import streamlit as st
from streamlit_option_menu import option_menu

# Use a custom container to control alignment and width
with st.sidebar:
    pass  # Ensure the sidebar doesn't interfere with layout

# Create space before the menu to push it right
st.markdown(
    """
    <style>
    .menu-container {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 30px;
    }
    .option-menu {
        width: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="menu-container">', unsafe_allow_html=True)

    selected = option_menu(
        None,
        ["Home", "Settings", "About"],
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0!important",
                "margin": "0!important",
                "background-color": "#fafafa",
                "width": "auto"
            },
            "icon": {"color": "orange", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0 10px",
                "padding": "10px 15px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#ddd"},
        }
    )

    st.markdown('</div>', unsafe_allow_html=True)

st.write(f"You selected: {selected}")
