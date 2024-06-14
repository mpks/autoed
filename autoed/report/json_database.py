import os
from autoed.constants import database_json_file, report_dir
import json


class JsonDatabase:

    def __init__(self, global_log_path):
        """
        Creates a json database file if it does not exists already

        global_log_path : path of string
            The json database is generated in the autoed report directory,
            along with the html report with processing statistics. The
            report directory is generated in the same directory as the global
            autoed log file.
        """

        report_path = os.path.join(global_log_path, report_dir)

        self.json_file = os.path.join(report_path, database_json_file)
        self.data = {}

        if not os.path.exists(self.json_file):
            if not os.path.exists(report_path):
                os.makedirs(report_path, exist_ok=True)
            with open(self.json_file, 'w') as file:
                json.dump({}, file)

    def load_data(self):
        with open(self.json_file, 'r') as file:
            self.data = json.load(file)

    def add_entry(self, dataset_name, value):
        """
        Add column data (value) for a dataset in the database

        dataset_name : string or path
        value : dict
            Can contain any keys, as long there is a key 'title',
            this key determines what is written at the top of the
            table column.
        """
        if dataset_name in self.data:         # Overwrite existing data
            self.data[dataset_name][value['title']] = value
        else:
            self.data[dataset_name] = {}
            self.data[dataset_name][value['title']] = value

    def save_data(self):
        with open(self.json_file, 'w') as file:
            json.dump(self.data, file)
