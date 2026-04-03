# Project Architecture

This is a Python application with:

- The main application code in `./plog` 
- Spikes for experimental development in `./spikes`
- Unit tests in `./tests`

The main application follows the model-controller-view design template:

- Models are in `./plog/models`
- Controllers are in `./plog/controllers`
- Views are in `./plog/pages`

# Dependencies

The application depends on the following software packages:

- Streamlit: https://docs.streamlit.io/
- streamlit-aggrid: https://github.com/PablocFonseca/streamlit-aggrid
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/
- sqlalchemy-history: https://github.com/corridor/sqlalchemy-history

# Coding Standards

The following coding standards shall be adhered to:

- Use Docstring format for documentation. Exclusively document code in English.
- Follow the existing naming conventions.
- Keep code simple and readable.
- Attempt to re-use code but not at the cost of readability.
- Take care of the correct indentation.
- Write unit tests for all controllers.

# Interface Design

The user interface is created with Streamlit. The following rules must be
respected when creating the interface:

- Use `st.aggrid` for the rendering of tables. The number of displayed rows 
shall be limited to `NUM_ROWS`. The default value of `NUM_ROWS`is 20. A scroll 
bar shall be shown on the right if the table contains more rows.
- Use `st_segmented_control` for the creation of toolbars. This is a builtin 
streamlit function (https://docs.streamlit.io/develop/api-reference/widgets/st.segmented_control). Add the same toolbar at the top and bottom of the page.
- Page reloads should be minimized.