# Air-pollution-anlaytics

Air Pollution and Respiratory Diseases Analysis

Study area: Nagpur, Maharashtra, India Problem statement: Understand the relationship between air pollution and respiratory diseases.

A beginner-friendly Python project that cleans air-pollution and hospital-admission data, calculates the Pearson correlation between them, finds the most affected age group, and shows everything in a Streamlit dashboard.

Demo Link
https://breathesafe-bygtuyl7wb35aqzpdh6nav.streamlit.app/

Setup and run (step by step)
Install Python 3.9 or newer from https://www.python.org/downloads/ (tick "Add Python to PATH" on Windows).
Open a terminal (Command Prompt / PowerShell / Terminal) and go to the project folder:
cd path/to/air_pollution_project
(Recommended) create a virtual environment:
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux
Install the libraries:
pip install -r requirements.txt
Start the dashboard:
streamlit run app.py
Your browser opens at http://localhost:8501. If it does not, open that address manually.
(Optional) To regenerate the sample files: python generate_sample_data.py

CSV formats (for the upload option)
Use the sidebar uploaders. Upload both files together.

Air pollution CSV

date	aqi	pm25	pm10
2024-01-01	150	80	160
Hospital admissions CSV

date	age_group	admissions
2024-01-01	Children (0-14)	120
Daily or monthly rows both work (the code groups everything by month).
Extra columns are ignored. Column names are not case-sensitive.
Use any age-group labels you like; the dashboard uses whatever is in the file.
What the code does
Step	Where	Details
Validate file	analysis.py	Checks required columns; clear error message if something is wrong
Clean	analysis.py	Bad dates removed; text/negative numbers treated as missing; pollution gaps filled by interpolation; admission gaps filled with the age-group median
Combine	analysis.py	Pollution averaged per month, admissions summed per month, joined on month
Correlation	analysis.py	scipy.stats.pearsonr for AQI, PM2.5 and PM10 vs total monthly admissions (r and p-value)
Age groups	analysis.py	Total admissions and share (%) per age group
Dashboard	app.py	Metrics, Plotly charts, correlation table, findings, recommendations, upload
Using real data (suggested sources)
Please check each site for the current download options and terms of use.

Air quality: Central Pollution Control Board (CPCB) air-quality portal, Maharashtra Pollution Control Board (MPCB), the open-data portal data.gov.in, or OpenAQ. Look for Nagpur monitoring stations.
Respiratory admissions: Government health data such as the Health Management Information System (HMIS), or records obtained with permission from hospitals / public health departments. Hospital data is often not openly available at city level, so you may need to request it formally. Never use patient-identifying data.
Limitations (mention these in your presentation)
Correlation is not causation. Weather, seasonal infections, and reporting practices also affect admissions.
Admissions by age group are raw counts, not rates. Using population figures would make the comparison fairer.
Monthly averages hide short pollution spikes.
The included sample data is synthetic and for demonstration only.
Presentation tips
Show the sample-data warning first and explain why it is there.
Walk through the pipeline: load → clean → merge by month → Pearson correlation → age groups → dashboard.
Upload a small test CSV to demonstrate flexible input, and an invalid file to show the friendly error message.
Finish with the recommendations and the limitations above.
