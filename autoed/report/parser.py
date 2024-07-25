"""Here we keep clases that parse xia2 and DIALS output files"""
from autoed.report.table_entry import PipelineEntry
from autoed.constants import xia2_pipelines
from autoed.constants import xia2_output_file
from autoed.constants import xia2_dials_report_path
from autoed.report.json_database import JsonDatabase
from autoed.utility.filesytem import find_files_in_directory
import re
import os


class Xia2OutputParser:

    def __init__(self, dataset, database: JsonDatabase):

        self.dataset = dataset
        self.database = database

    def add_to_database(self):

        dataset_name = self.dataset.base

        for pipeline_name in xia2_pipelines:

            xia2_path = os.path.join(self.dataset.output_path, pipeline_name)

            # For older datasets, the output of default pipeline went
            # directly in the processed directory and not in a separate
            # (e.g. 'default') directory. The folowing line is just to process
            # those datasets
            if pipeline_name == 'default':
                if not os.path.exists(xia2_path):
                    xia2_path = self.dataset.output_path

            xia2_file = os.path.join(xia2_path, xia2_output_file)

            table_entry = self._parse_output(xia2_file, pipeline_name)
            table_entry = table_entry.to_dict()
            self.database.add_entry(dataset_name, table_entry,
                                    self.dataset.beam_figure)
            self.database.save_data()

    def _parse_output(self, xia2_file, pipeline):

        if not os.path.exists(xia2_file):
            return PipelineEntry(title=pipeline,
                                 status='no_data',
                                 tooltip='No xia2 output file')

        if is_xia2_output_ok(xia2_file):

            values = parse_xia2_txt_file(xia2_file)
            n_tot, n_indexed = parse_xia2_indexed_stats(xia2_file)

            if len(values) != 7:
                return PipelineEntry(title=pipeline,
                                     status='parse_error',
                                     tooltip='Failed to parse xia2 output')

            tooltip = "unit cell: "
            tooltip += f"{values[0]:.2f}  {values[1]:.2f}  {values[2]:.2f} \n"
            tooltip += "angles: "
            tooltip += f"{values[3]:.2f}  {values[4]:.2f}  {values[5]:.2f} \n"
            tooltip += f"space group: {values[6]}"

            report_file = xia2_file.replace('txt', 'html')

            return PipelineEntry(title=pipeline,
                                 status='OK',
                                 indexed=n_indexed,
                                 total_spots=n_tot,
                                 unit_cell=values[0:6],
                                 space_group=values[-1],
                                 link=report_file,
                                 tooltip=tooltip)

        # Catch with which error it failed
        error_msg = parse_xia2_error(xia2_file)

        return PipelineEntry(title=pipeline,
                             status='process_error',
                             tooltip=error_msg)

    def update_database(self):
        pass


def is_xia2_output_ok(xia2_file):
    """Checks if xia2 processing completed normally"""

    normal_status = "Status: normal termination"
    with open(xia2_file, 'r') as file:
        for line in file:
            if normal_status in line:
                return True
    return False


def parse_xia2_error(xia2_file):
    """Get the error line from the xia2 output file"""

    error_status = "Error:"
    with open(xia2_file, 'r') as file:
        for line in file:
            if error_status in line:
                return line
    return 'Error not parsed correctely.'


def parse_dials_indexed_stats(dials_index_file):
    """Returns the total number of spots, and the number of indexed"""

    with open(dials_index_file, 'r') as file:
        lines = file.readlines()

    search_str = 'Saving refined experiments to'

    found = False
    for index, line in enumerate(lines):
        if search_str in line:
            found = True
            break

    if not found:
        return None

    stat_line = lines[index - 2]

    vals = stat_line.split("|")
    try:
        indexed = int(vals[2])
        unindexed = int(vals[3])
    except ValueError:
        return None

    return indexed + unindexed, indexed


def parse_xia2_indexed_stats(xia2_file):

    dials_index_file = find_xia2_dials_indexed_log_file(xia2_file)

    if dials_index_file:
        if os.path.exists(dials_index_file):
            stats = parse_dials_indexed_stats(dials_index_file)
            if stats:
                n_tot, n_indexed = stats

                if n_tot == 0:
                    return None, None

                return n_tot, n_indexed
            else:
                return None, None
        return None, None
    return None, None


def sort_dials_index_files(dials_index_files):
    """Given a list of files with names ##_dials.index.log it sorts them
    according to the number they start with
    """

    if len(dials_index_files) == 0:
        return None
    if len(dials_index_files) == 1:
        return dials_index_files[0]

    if 'dials.index.log' in dials_index_files:
        dials_index_files.remove('dials.index.log')
        indices = []
        for file in dials_index_files:
            index = int(file.split('_')[0])
            indices.append(index)

        combined = list(zip(indices, dials_index_files))
        combined_sorted = sorted(combined)
        indices_sorted, index_files_sorted = zip(*combined_sorted)
        return index_files_sorted[-1]


def find_xia2_dials_indexed_log_file(xia2_file):
    """Searches the xia2 output for the last dials indexing log file"""

    xia2_path = os.path.dirname(xia2_file)
    dials_output_path = os.path.join(xia2_path, xia2_dials_report_path)

    if os.path.exists(dials_output_path):

        dials_index_files = find_files_in_directory(dials_output_path,
                                                    '*dials.index.log')
        dials_index_file = sort_dials_index_files(dials_index_files)

        dials_index_file = os.path.join(dials_output_path, dials_index_file)

        return dials_index_file

    return None


def parse_xia2_txt_file(xia2_file):
    """Get data on unit cell and space group"""

    with open(xia2_file, 'r') as file:
        lines = file.readlines()

    match_index = None
    match_uc_str = 'Unit cell (with estimated std devs):'

    for i, line in enumerate(lines):     # Find the last occurence
        if match_uc_str in line:
            match_index = i

    if not match_index:
        return None

    vectors_str = lines[match_index + 1].strip()
    angles_str = lines[match_index + 2].strip()
    space_group_str = lines[match_index - 1].strip()

    vectors = extract_floats(vectors_str)
    angles = extract_floats(angles_str)
    space_group = extract_space_group(space_group_str)
    vectors.extend(angles)
    vectors.extend([space_group])

    return vectors


def extract_space_group(string):
    """Get space group string"""

    test_str = 'Assuming spacegroup:'
    if test_str in string:
        parts = string.split(':', 1)
        return parts[1]
    return None


def extract_floats(string):
    """Return all floats in a string as a list"""

    # Remove all blocks with brackets containing numbers
    modified_string = re.sub(r'\(\d+\)', ' ', string)

    # Find all floats or ints
    float_pattern = r'\b\d+\.\d+|\b\d+'
    matches = re.findall(float_pattern, modified_string)

    return [float(match) for match in matches]
