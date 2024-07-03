"""Here we keep clases that parse xia2 and DIALS output files"""
from autoed.report.table_entry import PipelineEntry
from autoed.constants import xia2_pipelines
from autoed.constants import xia2_output_file
from autoed.report.json_database import JsonDatabase
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
            xia2_file = os.path.join(xia2_path, xia2_output_file)

            table_entry = self._parse_output(xia2_file, pipeline_name)
            table_entry = table_entry.to_dict()
            self.database.add_entry(dataset_name, table_entry)
            self.database.save_data()

    def _parse_output(self, xia2_file, pipeline):

        if not os.path.exists(xia2_file):
            return PipelineEntry(title=pipeline,
                                 status='no_data',
                                 tooltip='No xia2 output file')

        if is_xia2_output_ok(xia2_file):

            values = parse_xia2_txt_file(xia2_file)

            if len(values) != 7:
                return PipelineEntry(title=pipeline,
                                     status='parse_error',
                                     tooltip='Failed to parse xia2 output')

            tooltip = "unit cell: "
            tooltip += f"{values[0]:.2f}  {values[1]:.2f}  {values[2]:.2f} \n"
            tooltip += "angles: "
            tooltip += f"{values[3]:.2f}  {values[4]:.2f}  {values[5]:.2f} \n"
            tooltip += f"space group: {values[6]}"

            return PipelineEntry(title=pipeline,
                                 status='OK',
                                 indexed=None,
                                 unit_cell=values[0:6],
                                 space_group=values[-1],
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
