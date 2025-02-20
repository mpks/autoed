import json
import argparse
import os


def main():

    msg = 'Generate a txt report file from the JSON database'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('database_file_path', type=str,
                        help='Path of the autoed_database.json file.')
    parser.add_argument('output_path', type=str,
                        help='Path where to save the generated txt report.')
    args = parser.parse_args()

    generate_txt_report(args.database_file_path, args.output_path)


def get_percentage(dataset):
    return dataset.get_index()


def generate_txt_report(json_database_file, output_path):

    with open(json_database_file, 'r') as f:
        data = json.load(f)

    datasets = []
    for dset, value in data.items():

        pipelines = []

        for key, val in value.items():
            if type(val) is dict:
                if 'title' in val:        # We are working with a pipeline
                    pipeline = val['title']
                    indexed = val['indexed']
                    total = val['total_spots']
                    unit_cell = val['unit_cell']
                    space_group = val['space_group']
                    dataset = Dataset(dset, indexed, total,
                                      pipeline, unit_cell, space_group)
                    pipelines.append(dataset)
        max_pipeline = max(pipelines, key=get_percentage, default=None)

        if max_pipeline:
            datasets.append(max_pipeline)

    sorted_datasets = sorted(datasets, key=get_percentage, reverse=True)

    sorted_datasets = [d for d in sorted_datasets if d.get_index() > 1.e-5]

    report_path = os.path.join(output_path, 'report.txt')
    sorted_report_path = os.path.join(output_path, 'report_sorted.txt')

    save_txt(report_path, datasets)
    save_txt(sorted_report_path, sorted_datasets)


def save_txt(filename, datasets):

    header = 130*'-' + '\n'
    header += '  N   |  Ind. %   | Indexed  |   Spots  |'
    header += '                 Unit cell                 |     Group  |'
    header += ' Dataset name \n'

    with open(filename, 'w') as f:

        f.write(header)
        for ind, dataset in enumerate(datasets):
            if ind % 5 == 0:
                f.write(130*'-' + '\n')
            f.write(f" {ind+1:04d} |")
            f.write(dataset.write_txt_one_line())


class Dataset:

    def __init__(self, name, indexed=None, total=None,
                 pipeline=None, unit_cell=None, space_group=None):
        self.name = name
        self.indexed = indexed
        self.total = total
        self.pipeline = pipeline
        self.unit_cell = unit_cell
        self.space_group = space_group

    def get_index(self):
        if self.indexed is not None and self.total is not None:
            return 100. * self.indexed / self.total
        else:
            return 0.0

    def write_txt_one_line(self):
        """Summarize the dataset in a single txt line"""

        out = ""
        out += f"  {self.get_index():>5.1f} %  "

        if self.indexed:
            out += f"|  {int(self.indexed):>6d}  "
        else:
            out += "|  ------  "

        if self.total:
            out += f"|  {int(self.total):>6d}  "
        else:
            out += "|  ------  "

        cell_str = "|    ----   ----   ----    ---   ---   ---  "
        if isinstance(self.unit_cell, list):
            if len(self.unit_cell) == 6:
                u = self.unit_cell
                out += f"|  {u[0]:>6.1f} {u[1]:>6.1f} {u[2]:>6.1f} "
                out += f" {u[3]:>5.1f} {u[4]:>5.1f} {u[5]:>5.1f}  "
            else:
                out += cell_str
        else:
            out += cell_str

        if self.space_group:
            out += f"| {self.space_group:>10} "
        else:
            out += "|       ---- "

        dataset_base = self.name.split('/')[-1]
        out += f"| {dataset_base} "

        out += "\n"
        return out


if __name__ == '__main__':
    main()
