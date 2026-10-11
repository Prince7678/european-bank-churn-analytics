# European Banking Customer Churn Analytics — Streamlit App

## Included files
- `app.py` — interactive dashboard
- `requirements.txt` — Python packages
- `European_Bank_Project_FINAL_fixed.xlsx` — workbook/data source

## Run locally
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run: `python -m pip install -r requirements.txt`
4. Run: `streamlit run app.py`
5. If the workbook isn't auto-detected, upload it from the sidebar.

The app reads the `European_Bank` raw-data sheet and derives segmentation groups inside the app. It does not depend on cached spreadsheet formulas.
