trigger_file = '.HiMarko'

xia2_pipelines = ['default', 'user', 'ice', 'real_space_indexing']
dials_pipelines = ['max_lattices']
all_pipelines = xia2_pipelines + dials_pipelines

xia2_output_file = 'xia2.txt'

report_path = 'AUTO'            # Generated at the same level as 'processed'

report_dir = 'autoed_report'
report_html_file = 'autoed_overview.html'
database_json_file = 'autoed_database.json'        # Keeps processing summaries
xia2_report_dir = 'xia2_reports'              # Keeps xia2 html reports
beam_report_dir = 'beam_positions'                 # Keeps beam images
xia2_dials_report_path = 'DEFAULT/NATIVE/SWEEP1/index'
ed_root_dir = 'ED'
