import subprocess
import webview
import threading

def start_streamlit():
    # Start the Streamlit app
    subprocess.run(["streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8501"])

# Start the Streamlit app in a separate thread
threading.Thread(target=start_streamlit).start()

# Create a PyWebView window
webview.create_window("Streamlit App", "http://localhost:8501", width=800, height=600)
#webview.create_window("Google App", "https://www.google.com", width=800, height=600)

# Start the PyWebView event loop
webview.start()