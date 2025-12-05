from src.processing.generate_playlist_csv_app import *
import sys
from streamlit.web import cli as stcli

if __name__ == "__main__":
    # This mimics the command 'streamlit run app.py'
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())