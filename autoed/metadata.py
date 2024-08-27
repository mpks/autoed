"""Everything related to reading metadata files"""
from __future__ import annotations
import re
import json


from autoed.utility.misc_functions import (
    electron_wavelength, scrap, get_detector_distance,
    is_file_fully_written,
)


class Metadata:
    """A class to keep all relevant experimental metadata"""

    def __init__(self):
        self.wavelength = 0.02507934052490744
        self.angle_increment = 0.5
        self.start_angle = -30.0
        self.detector_distance = 785.91
        self.sample_type = 'macro'
        self.unit_cell = None
        self.space_group = None

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

        if 'wavelength' not in json_data:
            dataset.logger.error('wavelength set to None in JSON file')
            return False
        self.wavelength = json_data['wavelength']

        if 'angle_increment' not in json_data:
            dataset.logger.error('angle_increment set to None in JSON file')
            return False
        self.angle_increment = json_data['angle_increment']

        if 'start_angle' not in json_data:
            dataset.logger.error('start_angle set to None in JSON file')
            dataset.logger.info('Trying to fetch start_angle from log file')

            success, start_angle = scrap(dataset.log_file, 'start angle',
                                         float, -60)
            if not success:
                return False
            else:
                dataset.logger.info(f"start_angle set to {start_angle}")
                self.start_angle = start_angle
        else:
            self.start_angle = json_data['start_angle']

        self.sample_type = json_data['sample_type']
        self.unit_cell = json_data['unit_cell']
        space_group = json_data['space_group']
        if space_group == "undefined":
            space_group = None
        self.space_group = space_group

        if 'detector_distance' not in json_data:
            dataset.logger.error('detector_distance not in JSON file')
            return False
        self.detector_distance = json_data['detector_distance']
        if self.detector_distance is None:
            dataset.logger.error('detector_distance set to None in JSON file')
            return False

        return True


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
