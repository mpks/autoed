"""Everything related to reading metadata files"""
from __future__ import annotations
import re
import json


from autoed.utility.misc_functions import (
    electron_wavelength, scrap, get_detector_distance,
    is_file_fully_written,
)

default_metadata = {}
default_metadata['wavelength'] = None
default_metadata['angle_increment'] = None
default_metadata['start_angle'] = None
default_metadata['detector_distance'] = None
default_metadata['sample_type'] = None
default_metadata['unit_cell'] = None
default_metadata['space_group'] = None
default_metadata['rotation_speed'] = None


class Metadata(dict):
    """A class to keep all relevant experimental metadata"""

    def __init__(self):

        for key, value in default_metadata.items():
            self[key] = value

    def from_txt(self, dataset):
        """Read the metadata from textual files (e.g. log, mdoc etc)

        Returns
        success : boolean
        """

        # Read metadata from mdoc file
        mdoc_written, _, _ = is_file_fully_written(dataset.mdoc_file)
        if not mdoc_written:
            dataset.logger.info('Conversion failed. mdoc file not complete')
            return False

        # Get voltage and wavelength
        success, voltage = scrap(dataset.mdoc_file, 'Voltage', float, 200.0)
        if not success:
            msg = "Failed to scrap the voltage. Setting it to default (200)"
            dataset.logger.warning(msg)
        else:
            dataset.logger.info(f"Voltage from mdoc file: {voltage}")
        self.wavelength = electron_wavelength(voltage)

        # Read metadata from the log file
        log_written, _, _ = is_file_fully_written(dataset.log_file)
        if not log_written:
            dataset.logger.info('Conversion failed. log file not complete')
            return False

        # Get start angle
        success, start_angle = scrap(dataset.log_file, 'start angle',
                                     float, -60)
        if not success:
            msg = "Failed to scrap the start angle from the log file\n."
            msg += f"Setting it to default {start_angle}"
            dataset.logger.warning(msg)
        else:
            msg = f"Start angle from the log file: {start_angle}"
            dataset.logger.info(msg)
        self.start_angle = start_angle

        # Get angle increment
        increment = get_angle_increment_old(dataset)

        if not increment:
            msg = "Failed to scrap the angle increment from the log file.\n"
            msg += "Trying for the new textual file format."
            dataset.logger.warning(msg)
            increment = get_angle_increment_new(dataset)

        if not increment:
            msg = "Failed to scrap the angle increment from the new format.\n"
            msg += "Using alternative method (end - start) / num_of_frames "
            dataset.logger.warning(msg)
            increment = get_angle_increment_alternative(dataset)

        if not increment:
            increment = 0.5
            msg = "Failed to scrap the angle increment.\n"
            msg += f"Setting the default value to {increment}"
            dataset.logger.warning(msg)

        msg = f"Setting the angle increment: {increment}"
        dataset.logger.info(msg)
        self.angle_increment = increment

        # Read detector distance from the PatchMaster file
        patch_written, _, _ = is_file_fully_written(dataset.patch_file)
        if not patch_written:
            dataset.logger.info('Conversion failed. Patch file not complete')
            return False
        self.detector_distance = get_detector_distance(dataset.patch_file)

        if self.detector_distance is None:
            dataset.logger.error('Detector distance is None.')
            return False

        return True

    def from_json(self, dataset):
        """Read the metadata from json file format"""

        json_written, _, _ = is_file_fully_written(dataset.json_file)

        if not json_written:
            dataset.logger.error('JSON file not complete')
            return False

        with open(dataset.json_file, 'r') as json_file:
            json_data = json.load(json_file)

        # First check if all the required metadata is in JSON file
        msg = "Reading required metadata from the JSON file"
        dataset.logger.info(msg)
        for key, value in self.items():
            if key not in json_data:
                msg = f"Required key '{key}' not in JSON metadata file"
                dataset.logger.error(msg)
                return False
            else:
                msg = f"  {key}: {json_data[key]}"
                dataset.logger.info(msg)
                self[key] = json_data[key]

        if self.space_group == "undefined":
            dataset.logger.info("Overwritting the space_group: to None")
            self.space_group = None

        if isinstance(self.rotation_speed, str):
            try:
                dataset.logger.info("Converting rotation_speed to float")
                self.rotation_speed = float(self.rotation_speed)
            except Exception:
                msg = "Failed to convert the rotation speed from the JSON "
                msg += "metadata file into a float"
                dataset.logger.error(msg)
                return False

        # Read any other metadata present in the metadata file
        msg = "Reading the rest of metadata from the JSON file"
        dataset.logger.info(msg)
        for key, value in json_data.items():
            if key not in default_metadata:
                msg = f"  {key}: {value}"
                dataset.logger.info(msg)
                self[key] = value

        return True

    def __getattr__(self, key):
        """Handle attribute access (obj.key)."""
        try:
            return self[key]
        except KeyError:
            msg = f"{self.__class__.__name__} object has no attribute '{key}'"
            raise AttributeError(msg)

    def __setattr__(self, key, value):
        """Handle attribute assignment (obj.key = value)."""
        self[key] = value

    def __delattr__(self, key):
        """Handle attribute deletion (del obj.key)."""
        try:
            del self[key]
        except KeyError:
            msg = f"{self.__class__.__name__} object has no attribute '{key}'"
            raise AttributeError(msg)


def get_angle_increment_old(dataset):
    """Scrap old data format and get the angle increment"""

    # Get speed_param
    success, speed_param = scrap(dataset.log_file, 'speed parameter',
                                 float, 0.033615008)
    if not success:
        msg = "Failed to scrap the speed_param from the log file.\n"
        msg += f"Setting it to default value: {speed_param}"
        dataset.logger.warning(msg)
    else:
        dataset.logger.info(f"speed_param from the log file: {speed_param}")

    # Get frame_rate
    success, frame_rate = scrap(dataset.log_file, 'frame rate', float, 10)
    if not success:
        msg = "Failed to scrap the frame rate from the log file.\n"
        msg += f"Setting it to default value: {frame_rate}"
        dataset.logger.warning(msg)
    else:
        dataset.logger.info(f"Frame rate from the log file: {frame_rate}")

    success, speed_line = scrap(dataset.log_file, 'rotationSpeed', str, None)

    if success:
        pattern = r'^(.*)\*(.*)\+(.*)\*10\^(.*)$'
        p = re.search(pattern, speed_line)
    else:
        p = False

    if p:
        rotation_speed = float(p.group(1)) * speed_param
        rotation_speed += (float(p.group(3)) * 10**(float(p.group(4))))
        dataset.logger.info(f"rotationSpeed from log file: {rotation_speed}")
        return rotation_speed / frame_rate

    return None


def get_angle_increment_alternative(dataset):
    """Compute the angle increment from the start and end angles"""

    s1, start_angle = scrap(dataset.log_file, 'start angle', float, -60)
    s2, end_angle = scrap(dataset.log_file, 'end angle', float, 60)

    s3, num_frames = scrap(dataset.log_file, 'number of frames', int, 1200)

    if not s3:         # Check if nomber of frames is in new format
        s3, num_frames = scrap(dataset.log_file, 'noFrames', int, 1200)

    if s1 and s2 and s3:
        return (end_angle - start_angle) / num_frames

    return None


def get_angle_increment_new(dataset):
    """Scrap the new textual file format and compute increment angle"""

    success_01, speed = scrap(dataset.log_file, 'degrees per second', float, 2)
    if not success_01:
        msg = "Failed to scrap `degrees per second` from new file format.\n"
        msg += f"Setting it to default value: {speed}"
        dataset.logger.warning(msg)
    else:
        dataset.logger.info(f"Speed set from the new format: {speed}")

    success_02, fps = scrap(dataset.log_file, 'fps', float, 4)

    if not success_02:
        msg = "Failed to scrap `fps` from new file format.\n"
        msg += f"Setting it to default value: {fps}"
        dataset.logger.warning(msg)
    else:
        dataset.logger.info(f"`fps` set from the new format: {fps}")

    if success_01 and success_02:
        return speed / fps
    return None
