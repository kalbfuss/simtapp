# Running Commands

- Always activate the python virtual environment with `source .venv/bin/activate` before running any commands.
- Test the streamlit application by running the command `pkill -f streamlit && source .venv/bin/activate && PYTHONPATH=. streamlit run plog/app.py`