# Basic validation to check if all required fields are present in the config file and to load it into the pipeline
# Given that we have the UI, this file could be omitted, but if the user directly edits the config file, then this is useful to make sure that all the necessary variables are there

import yaml

REQUIRED_FIELDS = {
	'dataset': ['input_path', 'output_path'],
	'columns': ['y_columns', 'id_columns', 'dp_columns', 'zip_code_column', 'drop_columns', 'plot_column'],
	'synthesis': ['methods', 'minnumlevels', 'maxfaclevels'],
	'evaluation': ['epsilon', 'sensitivity', 'sample_per', 'memory'],
	'environment': ['rscript_loc', 'synthpop_file']
}

def load_config(path):
	with open(path, 'r') as f:
		config = yaml.safe_load(f)
    
	for section, fields in REQUIRED_FIELDS.items():
		if section not in config:
			raise ValueError(f"Missing required section in config.yaml: '{section}'")
		for field in fields:
			if field not in config[section]:
				raise ValueError(f"Missing required field in config.yaml: '{section}.{field}'")
    
	return config