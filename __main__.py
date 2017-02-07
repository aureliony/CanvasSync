#!/usr/bin/env python2.7

"""
CanvasSync by Mathias Perslev

MSc Bioinformatics, University of Copenhagen
February 2017
"""

"""
__main__.py, main module

Implements the main module of CanvasSync. This module initiates the top-level Synchronizer object with the
settings specified in the settings file. If no settings file can be found, the user is promoted to supply the following
information:

1) A path to with synchronization will occur. The path must be pointing to a valid folder and contain a sub folder name.
   The sub folder is generated and stores all synchronized courses.
2) The domain_ of the Canvas web server.
3) An authentication token_ used to authenticate with the Canvas API. The token_ is generated on the Canvas web server
   after authentication under "Settings".

The main module may take input from the command line and will act accouringly. Without command line arguments,
CanvasSync will either do a first-time setup of the settings file (described above) or start synchronizing with settings
specified in the settings file.

The module takes the arguments -h or --help that will show a help screen and quit.
The module takes the arguments -i or --info that will show the currently logged settings from the settings file.
The module takes the arguments -s or --setup that will force CanvasSync to prompt the user for settings.
"""

# Inbuilt modules
import getopt
import os
import sys

# Add the CanvasSync module to the path variable at run time
sys.path.insert(0, os.path.split(os.path.split(os.path.abspath(__file__))[0])[0])

# CanvasSync modules
from CanvasSync.Hierarchy.synchronizer import Synchronizer
from CanvasSync.Statics.ANSI import Colors
from CanvasSync.Settings.settings import Settings
from CanvasSync.Statics.instructure_api import InstructureApi
from CanvasSync import usage


def run_canvas_sync():
    # Get command line arguments (C-style)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hsi", ["help", "setup", "info"])
    except getopt.GetoptError as err:
        # print help information and exit
        print str(err)
        usage.help()

    # Parse the command line arguments and act accordingly
    setup = False
    show_info = False
    if len(opts) != 0:
        for o, a in opts:
            if o in ("-h", "--help"):
                # Show help
                usage.help()

            elif o in ("-s", "--setup"):
                # Force re-setup
                setup = True

            elif o in ("-i", "--info"):
                # Show current settings
                show_info = True

            else:
                # Unknown option
                assert False, "Unhandled option"

    # Initialize Settings object. This object will parse the settings file or generate a new one if one does not exist.
    settings = Settings()

    # If the settings file does not exist or the user promoted to re-setup, start prompting user for settings info.
    if not settings.settings_file_exists() or setup:
        try:
            settings.set_settings()
        except KeyboardInterrupt:
            print Colors.RED + "\n\n[*] Setup interrupted" + Colors.ENDC
            sys.exit()

    # Load the settings currently in the settings file
    if not settings.is_loaded():
        settings.load_settings()

    # If -i or --info was specified, show the current settings and EXIT
    if show_info:
        settings.print_settings(clear=False)
        sys.exit(0)

    # Initialize the Instructure Api object used to make API calls to the Canvas server
    api = InstructureApi(settings)

    # Start Synchronizer with the current settings
    synchronizer = Synchronizer(settings=settings, api=api)
    synchronizer.sync()

    print Colors.BOLD + "\n\n[*] Sync complete" + Colors.ENDC


# If main module
if __name__ == "__main__":
    try:
        run_canvas_sync()
    except KeyboardInterrupt:
        print Colors.RED + "\n\n[*] Synchronization interrupted" + Colors.ENDC
        sys.exit()
