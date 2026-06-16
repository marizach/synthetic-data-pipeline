import streamlit as st
import pandas as pd
import yaml 
import pathlib
import os
from streamlit_sortables import sort_items
import subprocess
import sys

st.set_page_config(layout="wide")

os.chdir(pathlib.Path(__file__).parent.parent)

st.title("Synthetic Data Generation Pipeline")

st.markdown("""
This user interface has been developed in order to provide an easier way of customising settings for generating synthetic data using the pipeline developed at the UMCG.

Below, you can choose the dataset you want to synthesise using synthpop, and then modify any settings such as the methods used for each column and the order of the synthesis. 

Once these settings are set, you can run the pipeline and find the produced results using the link at the bottom of this page. 
""")


st.header("1. Dataset Specification")

folder_path = st.text_input("Input folder name")
st.caption("Enter the name of the folder in which your datasets are in (e.g. Inputs). Then a dropdown menu will appear below in which you can choose your desired input dataset file.")
columns = []
if folder_path:
  folder = pathlib.Path(folder_path)
  if folder.exists() and folder.is_dir():
    csv_files = list(folder.glob("*.csv"))
    if csv_files:
      selected_file = st.selectbox(
        "Select input file",
        options=[f.name for f in csv_files],
        index=0
      )
      # Read first row of data set and save column names
      input_path = str(folder / selected_file)
      df_preview = pd.read_csv(input_path, nrows=1) 
      columns = df_preview.columns.tolist() 
    else:
      st.error("No CSV files found in this folder")
  else:
    st.error("Folder not found - check your path")


output_path = st.text_input("Output path")
st.caption("The path where the results will be saved. This should be a folder. The app will create a subfolder with the name of the dataset and save the results there.")

st.divider()


st.header("2. Synthesis Configuration")

visit_sequence = []
used_columns = []

# Columns which will be dropped from the synthesis
drop_columns = st.multiselect("Select columns to drop", options=columns, default=[])
st.caption("Columns which will be dropped from the synthesis")

active_columns = [col for col in columns if col not in drop_columns]

# Removing the columns that were dropped from the visit sequence
if "visit_sequence" not in st.session_state or st.session_state.visit_sequence == []:
    st.session_state.visit_sequence = active_columns
else:
  # Remove dropped columns
  st.session_state.visit_sequence = [
    col for col in st.session_state.visit_sequence if col in active_columns
  ]
  # Add columns back if they are removed from dropped columns
  for col in active_columns:
    if col not in st.session_state.visit_sequence:
      st.session_state.visit_sequence.append(col)

st.subheader("Visit Sequence")
st.caption("Drag and drop the columns to set the order in which they will be synthesised.")
visit_sequence = sort_items(st.session_state.visit_sequence, direction="vertical")
st.session_state.visit_sequence = visit_sequence


st.subheader("Synthesis Methods")
st.caption("Select the synthesis method for each column.")

valid_methods = ["cart", "norm", "normrank", "logreg", "polyreg", "polr", "sample", "passive"]
methods = {}

for column in active_columns:
  methods[column] = st.selectbox(
    f"{column}",
    options=valid_methods,
    index=0,
    key=f"method_{column}"
)

st.subheader("Synthesis Parameters")
minnumlevels = st.number_input("Minimum number of levels", value=10)
st.caption("Minimum number of unique values a variable must have to be treated as numeric rather than categorical. This field has a default value. Please do not change if you are unsure about what it does.")

maxfaclevels = st.number_input("Maximum factor levels", value=60)
st.caption("Maximum number of levels allowed for categorical variables. This field has a default value. Please do not change if you are unsure about what it does.")

st.divider()

st.header("3. Evaluation Metrics Configuration")

if columns:

  # Y columns are the columns in the dataset for which the utility score will be calculated (default: age, gender).
  y_columns = st.multiselect("Select Y columns", options=columns, default=[])
  st.caption("Y columns are the columns in the dataset for which the utility score will be calculated")

  # ID columns are the columns in the dataset for which additional privacy scores will be calculated (default: age, gender, zip_code)
  id_columns = st.multiselect("Select ID columns", options=columns, default=[])
  st.caption("ID columns are the columns in the dataset for which additional privacy scores will be calculated")

  if len(id_columns) < 2:
    st.warning("Please select at least 2 ID columns for the privacy calculation to work.")

  # Differential Privacy columns
  dp_columns = st.multiselect("Select DP columns", options=columns, default=[])
  st.caption("DP columns are the columns in the dataset for which differential privacy will be applied during synthesis")

  non_numeric_dp = [c for c in dp_columns if df_preview[c].dtype == 'object']
  if non_numeric_dp:
    st.error(f"The following DP columns are not numeric: {', '.join(non_numeric_dp)}")

  # Variables used for drawing the graphs, col is the column which will be plotted for both the map and the distribution
  plot_col = st.selectbox("Select column for plotting", options=columns, index=0)
  st.caption("Column for plotting")

zip_code_col = st.selectbox(
  "Select zip code column", 
  options=["None"] + columns, 
  index=0,
  key="zip_code_col"
)
st.caption("The name of the column containing the zip_code data. Select 'None' if the dataset does not contain zip code data.")

# Convert "None" string to actual None
if zip_code_col == "None":
  zip_code_col = None

st.divider()


epsilon = st.number_input("Epsilon", value=0.8)
st.caption("Privacy budget for differential privacy. Lower values mean stronger privacy but more noise. Default: 0.8")

sensitivity = st.number_input("Sensitivity", value=1.0)
st.caption("Maximum influence a single record can have on the output, used in Laplace noise calculation. Default: 1")

sample_per = st.number_input("Sample per", value=75)
st.caption("Percentage of the dataset sampled when calculating privacy scores. Default: 75")


st.divider()

# Advanced settings section, user does not need to always change these

# Auto-detect Python path in the conda environment created for this pipeline (named "sdp" based on the technical note)
conda_root = pathlib.Path(sys.executable).parent.parent
# Windows path
sdp_python_win = conda_root / "envs" / "sdp" / "python.exe" 
# Mac/Linux path     
sdp_python_unix = conda_root / "envs" / "sdp" / "bin" / "python"  

if sdp_python_win.exists():
    python_default = str(sdp_python_win)
elif sdp_python_unix.exists():
    python_default = str(sdp_python_unix)
else:
    python_default = sys.executable

# Auto-detect Rscript location
# First check RSCRIPT_PATH environment variable (set by user on myDRE based on technical note)
# If not, check the default Mac/Linux location
# If not, check 'where' (Windows) or 'which' (Mac/Linux)
if os.environ.get('RSCRIPT_PATH'):
    rscript_default = os.environ.get('RSCRIPT_PATH')
elif pathlib.Path('/usr/local/bin/Rscript').exists():
    rscript_default = '/usr/local/bin/Rscript'
else:
    which_cmd = 'where' if os.name == 'nt' else 'which'
    result = subprocess.run([which_cmd, 'Rscript'], capture_output=True, text=True)
    rscript_default = result.stdout.strip()

# Default kernel name (based on the technical note)
kernel_default = "sdp"

# Relative path to synthpop R script
synthpop_default = "R_scripts/synthpop_script.R"

# All the advanced settings are hidden in an expandable section
with st.expander("Advanced settings"):
  st.caption("These settings are auto-detected and should not need to be changed.")
  rscript_loc = st.text_input("Rscript location", value=rscript_default)
  st.caption("Path to the Rscript executable. Auto-detected from RSCRIPT_PATH environment variable or default locations.")
  synthpop_file = st.text_input("Synthpop script location", value=synthpop_default)
  st.caption("Relative path to the synthpop R script.")
  python_path = st.text_input("Python executable path", value=python_default)
  st.caption("Path to the Python executable in your conda environment.")
  kernel_name = st.text_input("Jupyter kernel name", value=kernel_default)
  st.caption("Name of the Jupyter kernel to use. Must match your conda environment name.")
  memory = st.number_input("Memory", value=400)
  st.caption("Memory limit in MB used during privacy calculations. Increase for large datasets. Default: 400")


if st.button("Run Pipeline"):

  # Creating the yaml configuration file
  config = {
    "dataset": {
      "input_path": input_path,
      "output_path": output_path
    },
    "columns": {
      "y_columns": y_columns,
      "id_columns": id_columns,
      "dp_columns": dp_columns,
      "drop_columns": drop_columns,
      "plot_column": plot_col,
      "zip_code_column": zip_code_col,
    },
    "synthesis": {
      "visit_sequence": visit_sequence,
      "methods": methods,
      "minnumlevels": minnumlevels,
      "maxfaclevels": maxfaclevels
    },
    "evaluation": {
      "epsilon": epsilon,
      "sensitivity": int(sensitivity),
      "sample_per": sample_per,
      "memory": memory
    },
    "environment": {
      "rscript_loc": rscript_loc,
      "synthpop_file": synthpop_file
    }
  }

  with open("config_ui.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)

  with st.spinner("The synthetic data pipeline is running... this may take a few minutes"):

    result = subprocess.run(
      [python_path, "-m", "jupyter", "nbconvert",
      "--to", "notebook",
      "--execute",
      f"--ExecutePreprocessor.kernel_name={kernel_name}",
      "--ExecutePreprocessor.timeout=600",
      "Generation_Evaluation_Template.ipynb"],
      capture_output=True, text=True
    )

    if result.returncode == 0:
      st.success("Synthesis completed successfully!")

      # Synthesised data is saved in the folder specified by the user
      st.info(f"You can find the synthesised data in: {output_path}")

      # Fidelity results
      fidelity_path = pathlib.Path(output_path) / "fidelity_results.csv"
      if fidelity_path.exists():
        st.subheader("Fidelity Results")
        st.dataframe(pd.read_csv(fidelity_path, index_col=0))

      # Fidelity ratio results
      fidelity_ratio_path = pathlib.Path(output_path) / "fidelity_ratio_results.csv"
      if fidelity_ratio_path.exists():
        st.subheader("Fidelity Ratio Results")
        st.dataframe(pd.read_csv(fidelity_ratio_path, index_col=0))

      # Privacy results
      privacy_path = pathlib.Path(output_path) / "privacy_results.csv"
      if privacy_path.exists():
        st.subheader("Privacy Results")
        st.dataframe(pd.read_csv(privacy_path, index_col=0))

      # Privacy results combined
      privacy_combined_path = pathlib.Path(output_path) / "privacy_results_combined.csv"
      if privacy_combined_path.exists():
        st.subheader("Privacy Results (with ratios)")
        st.dataframe(pd.read_csv(privacy_combined_path, index_col=0))

      # Privacy results ID
      privacy_id_path = pathlib.Path(output_path) / "privacy_results_id.csv"
      if privacy_id_path.exists():
        st.subheader("Privacy Results (quasi-identifiers)")
        st.dataframe(pd.read_csv(privacy_id_path, index_col=0))

      # Privacy results ID combined
      privacy_id_combined_path = pathlib.Path(output_path) / "privacy_results_id_combined.csv"
      if privacy_id_combined_path.exists():
        st.subheader("Privacy Results (quasi-identifiers with ratios)")
        st.dataframe(pd.read_csv(privacy_id_combined_path, index_col=0))

      # Regression results
      st.subheader("Regression Results")
      for metric in ["r2", "mean_squared_error", "max_error", "explained_variance_score"]:
        regression_path = pathlib.Path(output_path) / f"regression_{metric}.csv"
        if regression_path.exists():
          st.write(f"**{metric}**")
          st.dataframe(pd.read_csv(regression_path, index_col=0))

      # Classification results
      st.subheader("Classification Results")
      for metric in ["accuracy", "recall", "precision", "f1"]:
        classification_path = pathlib.Path(output_path) / f"classification_{metric}.csv"
        if classification_path.exists():
          st.write(f"**{metric}**")
          st.dataframe(pd.read_csv(classification_path, index_col=0))

      # displaying the scores in the UI
      end_score_path = pathlib.Path(output_path) / "end_score.csv"
      if end_score_path.exists():
        st.subheader("Final Scores")
        st.dataframe(pd.read_csv(end_score_path, index_col=0))


      plots_dir = pathlib.Path(output_path) / "plots"
      if plots_dir.exists():
        map_plots = sorted(plots_dir.glob("map_*.png"))
        if map_plots:
          st.subheader("Geographical Plots")
          for img_path in map_plots:
            st.image(str(img_path))
          
        dist_plots = sorted(plots_dir.glob("dist_*.png"))
        if dist_plots:
          st.subheader("Distribution Plots")
          for img_path in dist_plots:
            st.image(str(img_path))
      
      # If synthpop gives any warnings we want to display them to the user
      r_warnings = [line for line in result.stderr.splitlines() if "Warning" in line or "warning" in line]
      if r_warnings:
        with st.expander("Synthpop warnings"):
          for w in r_warnings:
            st.warning(w)
    else:
      st.error("Synthesis failed.")

      # Errors from the notebook shown in the UI
      stderr_lines = result.stderr.splitlines()
      stderr_section = []
      capture = False
      for line in stderr_lines:
        if "STDERR:" in line:
          capture = True
          continue
        if capture:
          stderr_section.append(line.strip())

      if stderr_section:
        st.subheader("What went wrong")
        for line in stderr_section:
          if not line:
            continue
          if line.startswith("Error"):
            st.error(line)
          elif "Execution halted" not in line:
            st.warning(line)

      with st.expander("Full error log", expanded=False):
        st.code(result.stderr, language="bash")