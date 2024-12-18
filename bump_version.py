#!/usr/bin/env python3
import os
import argparse
import subprocess


def main():

    msg = 'Update bump version and commit with the tag'
    parser = argparse.ArgumentParser(description=msg)

    msg = "Either 'major', 'minor', 'patch', or 'post"
    parser.add_argument('which', type=str, help=msg)

    args = parser.parse_args()

    file1 = VersionedFile('setup.py')
    file2 = VersionedFile('./autoed/__init__.py')

    version = file1.get_version()

    new_version = update_version(version, which=args.which)

    file1.update(new_version)
    file2.update(new_version)
    message = f'"Bump version: {version} -> {new_version}"'
    print(message)

    cmd1 = f'git add -u'
    cmd2 = f'git commit -m {message}'
    cmd3 = f'git tag v{new_version}'

    result = subprocess.run(cmd1, shell=True, capture_output=True, text=True)
    result = subprocess.run(cmd2, shell=True, capture_output=True, text=True)
    result = subprocess.run(cmd3, shell=True, capture_output=True, text=True)

class VersionedFile:

    def __init__(self, filename):

        self.file = os.path.abspath(filename)

        with open(self.file, 'r') as file:
            self.lines = file.readlines()

        version_line_index = None
        version_line = None
        for ln_index, line in enumerate(self.lines):
            if 'version' in line and '=' in line:
                version_line_index = ln_index
                version_line = line
                break

        self.version_line_index = version_line_index
        self.version_line = version_line

    def get_version(self):
        version = self.version_line.split('=')[1].strip().replace(',', '')
        version = version.replace("'", "")
        return version

    def update(self, new_version):

        new_version_line = self.version_line.split('=')[0]

        if ' = ' in self.version_line:
            new_version_line += '= ' + f"'{new_version}'"
        else:
            new_version_line += '=' + f"'{new_version}'"

        if ',' in self.version_line:
            new_version_line += ",\n"
        else:
            new_version_line += "\n"
        self.lines[self.version_line_index] = new_version_line

        with open(self.file, 'w') as file:
            for line in self.lines:
                file.write(line)


def update_version(version, which='patch'):

    version = version.replace("'", "")
    components = version.split('.')
    n = len(components)

    if not (n == 3 or n == 4):
        raise ValueError(f'Version format: {version} not recognized')

    post_index = 0
    if n == 4:
        post_index = int(components[3].replace('post', ''))

    major = int(components[0])
    minor = int(components[1])
    patch = int(components[2])

    if which == 'patch':
        out_version = f'{major}.{minor}.{patch + 1}'
    elif which == 'minor':
        out_version = f'{major}.{minor + 1}.0'
    elif which == 'major':
        out_version = f'{major+1}.0.0'
    elif which == 'post':
        out_version = f'{major}.{minor}.{patch}.post{post_index+1}'
    else:
        raise ValueError(f'which = "{which}" not recognized')

    return out_version


if __name__ == '__main__':
    main()
