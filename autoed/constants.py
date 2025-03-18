autoed_config_var = 'AUTOED_CONFIG_FILE'
autoed_config_file = 'autoed_config.json'
slurm_file = 'slurm_config.json'
xia2_pipelines = ['default', 'user', 'ice', 'real_space_indexing', 'xds']
dials_pipelines = ['max_lattices']
all_pipelines = xia2_pipelines + dials_pipelines
xia2_output_file = 'xia2.txt'
report_dir = 'autoed_report'
multiplex_dir = 'multiplex'                       # Where to copy all the files
multiplex_output_dir = 'xia2_multiplex_output'    # Where to keep the results
multiplex_default_sample = 'default_sample'
database_json_file = 'autoed_database.json'   # Keeps processing summaries
xia2_report_dir = 'xia2_reports'              # Keeps xia2 html reports
beam_report_dir = 'beam_positions'                 # Keeps beam images
spots_report_dir = 'spots'                         # Keeps spots
xia2_dials_report_path = 'DEFAULT/NATIVE/SWEEP1/index'
report_data_dir = 'report_data'
PROCESS_DONE_TRIGGER = '.done'


SINGLA_GAP_START = 510
SINGLA_GAP_STOP = 550
MID_START = 0.2    # Start of the midpoint intersection range (from 0 to 1)
MID_STOP = 0.9     # End of the midpoint intersection range   (from 0 to 1)
MID_STEP = 0.02     # Midpoint intersection range step (from 0 to 1)
BAD_PIXEL_THRESHOLD = 200000
