""" Contains global configuration dictionary """
from autoed.constants import (autoed_config_var, autoed_config_file)
import json
import os

default_global_config = {}
default_global_config['inotify'] = False
default_global_config['sleep_time'] = 1.
default_global_config['dummy'] = False
default_global_config['local'] = False
default_global_config['log_dir'] = None
default_global_config['gain'] = 1.
default_global_config['overwrite_mask'] = False
default_global_config['trigger_file'] = '.HiMarko'
default_global_config['ed_root_dir'] = 'ED'
default_global_config['processed_dir'] = 'processed'  # !CHANGE IN dataset


class GlobalConfig(dict):

    """A global configuration dictionary (with some extra features)"""

    def __init__(self):

        for key, value in default_global_config.items():
            self[key] = value

    def save_to_json(self, filename):
        """ Saves the configuration dictionary to JSON file """
        dict_entries = {key: value for key, value in self.items()}

        with open(filename, 'w') as f:
            json.dump(dict_entries, f, indent=4)

    def overwrite_from_local_config(self):
        """"
        Checks if there is an environment variable (e.g.  AUTOED_CONFIG_FILE)
        that contains the path to local JSON configuration file.

        If there is no environment variable, the default arguments remain
        unchanged.

        Returns
        -------
        log : string
            Used to write a log message that is latter passed to logger.
        """

        config_file = os.getenv(autoed_config_var)
        log = ""
        bfr = 31*" "

        if not config_file:
            log = "Local configuration file not set up.\n"
            log += bfr + "Using the default configuration."
            return log

        else:   # The variable is there, but the actual file might be missing
            if not os.path.isfile(config_file):
                log = f"Configuration file not found: '{config_file}'.\n"
                log += bfr + "Using the default configuration."
                return log
            else:

                with open(config_file, 'r') as f:
                    local_config_data = json.load(f)

                log = f"Found configuration file: '{config_file}'\n"
                msg = bfr + "Overwriting the default global parameters\n"
                msg += bfr + "with the ones from the configuration file:"

                header = False

                # Go through the global variables and check which is modified
                for key, value in self.items():
                    if key in local_config_data:
                        local_value = local_config_data[key]
                        if local_value != value:
                            if not header:
                                log += msg
                                header = True
                            log += '\n' + bfr + f"   {key}: "
                            log += f"{local_value}"
                            log += f"  (old value: {value})"
                            self[key] = local_value
        return log

    def print_to_log(self, logger):

        logger.info('Listing current global configuration: ')
        for key, value in self.items():
            logger.info(f"    {key}: {value} ")

    def overwrite_from_commandline(self, parsed_args):
        """Overwrite object dict values with the ones from the command line"""

        bfr = 31*" "
        args_dict = vars(parsed_args)
        header = False
        log = ''
        msg = "Overwriting global parameters with the ones from "
        msg += "the command line."

        for key, value in self.items():
            if key in args_dict:
                if args_dict[key]:      # The arg is not None (the user set it)

                    if not header:
                        log = msg
                        header = True
                    log += '\n' + bfr + f"  {key}: {args_dict[key]}  "
                    log += f"(old value: {value})"
                    self[key] = args_dict[key]
        return log

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


# A Singleton object to keep the global configuration
global_config = GlobalConfig()


def save_default():
    """Used on the commandline as 'autoed_generate_config' """

    print(50*'-')
    print(" Generating AutoED default configuration file")
    print(50*'-')
    with open(autoed_config_file, 'w') as f:
        json.dump(default_global_config, f, indent=4)

    print(f" Default configuration saved in '{autoed_config_file}'")
    print(f' Set system variable {autoed_config_var} with\n')
    msg = f' export {autoed_config_var}=/path/to/{autoed_config_file}\n'
    print(msg)
    print(' in your .bashrc to enable AutoED to find your config file.')
