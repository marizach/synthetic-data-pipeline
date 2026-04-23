import streamlit as st
import pandas as pd
import yaml 
import pathlib
import os
from streamlit_sortables import sort_items
import subprocess


os.chdir(pathlib.Path(__file__).parent.parent)


st.header("1. Dataset Configuration")

dataset_name = st.text_input("Dataset name")
input_path = st.text_input("Input path")

columns = []
if input_path:
  if pathlib.Path(input_path).exists():
    st.success("✓ File found")
    columns = pd.read_csv(input_path, nrows=0).columns.tolist()
  else:
    st.error("File not found - check your path")

output_path = st.text_input("Output path")

st.divider()

st.header("2. Column Configuration")

if columns:

  # Y columns are the columns in the dataset for which the utility score will be calculated (default: age, gender).
  y_columns = st.multiselect("Select Y columns", options=columns, default=[])
  st.caption("Y columns are the columns in the dataset for which the utility score will be calculated")

  # ID columns are the columns in the dataset for which additional privacy scores will be calculated (default: age, gender, zip_code)
  id_columns = st.multiselect("Select ID columns", options=columns, default=[])
  st.caption("ID columns are the columns in the dataset for which additional privacy scores will be calculated")

  # Differential Privacy columns
  dp_columns = st.multiselect("Select DP columns", options=columns, default=[])
  st.caption("DP columns are the columns in the dataset for which differential privacy will be applied during synthesis")

  # Columns which will be dropped from the synthesis
  drop_columns = st.multiselect("Select columns to drop", options=columns, default=[])
  st.caption("Columns which will be dropped from the synthesis")

  # Variables used for drawing the graphs, col is the column which will be plotted for both the map and the distribution
  plot_col = st.selectbox("Select column for plotting", options=columns, index=0)
  st.caption("Column for plotting")

# this needs to be changed later
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

st.header("3. Synthesis Configuration")

st.subheader("Visit Sequence")
st.caption("Select the position for each column in the synthesis order.")

visit_sequence = []
used_columns = []


if "visit_sequence" not in st.session_state or st.session_state.visit_sequence == [] or set(st.session_state.visit_sequence) != set(columns):
  st.session_state.visit_sequence = columns

st.subheader("Visit Sequence")
st.caption("Drag and drop the columns to set the order in which they will be synthesised.")
visit_sequence = sort_items(st.session_state.visit_sequence, direction="vertical")
st.session_state.visit_sequence = visit_sequence


st.subheader("Synthesis Methods")
st.caption("Select the synthesis method for each column.")

valid_methods = ["cart", "norm", "normrank", "logreg", "polyreg", "polr", "sample", "passive"]
methods = {}

for column in columns:
  methods[column] = st.selectbox(
    f"{column}",
    options=valid_methods,
    index=0,
    key=f"method_{column}"
)
  
# fix this section later with a better explanation
st.subheader("Synthesis Parameters")
minnumlevels = st.number_input("Minimum number of levels", value=10)
st.caption("Minimum number of unique values a variable must have to be treated as numeric rather than categorical.")

maxfaclevels = st.number_input("Maximum factor levels", value=60)
st.caption("Maximum number of levels allowed for categorical variables.")

st.divider()

st.header("4. Evaluation")
st.caption("Some caption about evaluation. Fix later")

epsilon = st.number_input("Epsilon", value=0.8)
sensitivity = st.number_input("Sensitivity", value=1.0)
sample_per = st.number_input("Sample per", value=75)
memory = st.number_input("Memory", value=400)

st.divider()

#Advanced settings section - Rscript location and synthpop script location

# Auto-detect Rscript location
result = subprocess.run(['which', 'Rscript'], capture_output=True, text=True)
rscript_default = result.stdout.strip()

# Auto-detect synthpop script location relative to ui/app.py
# synthpop_default = str(pathlib.Path(__file__).parent.parent / "R_scripts" / "synthpop_script.R")

synthpop_default = "R_scripts/synthpop_script.R"

with st.expander("Advanced settings"):
  st.caption("These settings are auto-detected and should not need to be changed.")
  rscript_loc = st.text_input("Rscript location", value=rscript_default)
  synthpop_file = st.text_input("Synthpop script location", value=synthpop_default)


# Generating config.yaml

if st.button("Generate config.yaml"):
  config = {
    "dataset": {
      "name": dataset_name,
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

  with open("config.yaml", "w") as f:
    yaml.dump(config, f, default_flow_style=False, sort_keys=False)
  st.success("config.yaml generated successfully!")