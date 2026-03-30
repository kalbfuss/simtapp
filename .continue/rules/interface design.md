# Interface Design

The user interface is created with Streamlit. The following rules must be 
respected when creating the interface:

- Use `st.aggrid` for the rendering of tables. The number of displayed rows 
shall be limited to `NUM_ROWS`. The default value of `NUM_ROWS`is 20. A scroll 
bar shall be shown on the right if the table contains more rows.
- Use `st_segmented_control` for the creation of toolbars. This is a builtin 
streamlit function. Add the same toolbar at the top and bottom of the page.
- Page reloads should be minimized.