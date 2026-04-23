# Basic validation design which can be extended later
# A question/decision to make: If I want further checks to be done here or if they can be done in the UI layer

import yaml

REQUIRED_FIELDS = {
    'dataset': ['name', 'input_path', 'output_path'],
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