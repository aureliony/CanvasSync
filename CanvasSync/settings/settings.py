"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

settings.py, Class

The Settings object implements the functionality of setting the initial-launch
settings and later loading these settings
These settings include:

1) A path to with synchronization will occur. The path must be pointing to a
   valid folder and contain a sub folder name.
   The sub folder is generated and stores all synchronized courses_to_sync.
2) The domain of the Canvas web server.
3) An authentication token used to authenticate with the Canvas API. The token
   is generated on the Canvas web server
   after authentication under "Settings".

The Settings object will prompt the user for these settings through the
set_settings method and write them to a hidden file in the users home directory.
The file is encrypted using a user-specified password. This password must
be specified whenever CanvasSync is launched. Encryption is implemented via
the PyCrypto AES-256 encryption module. The password is stored locally in a
hashed format using the bcrypt module. At runtime, the hashed password is used
to validate the user input password.
"""

# TODO
# - Clean things
# - Implement ANKI.fomrat method instead of accessing the ANKI attributes
#   directly
# - Make it possible reuse settings, so that you do not have to
#   re-specify all settings to change a single one

# Inbuilt modules
import os
import sys

from CanvasSync.settings import user_prompter

# CanvasSync modules
from CanvasSync.settings.cryptography import decrypt, encrypt
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI
from CanvasSync.utilities.instructure_api import InstructureApi


class Settings(object):
    def __init__(self):
        self.sync_path = "Not set"
        self.domain = "Not set"
        self.token = "Not set"
        self.courses_to_sync = ["Not set"]
        self.modules_settings = {"Files": True,
                                 "HTML pages": True,
                                 "External URLs": True}
        self.sync_assignments = True
        self.download_linked = True
        self.avoid_duplicates = True
        self.use_nicknames = False

        # Get the path pointing to the settings file.
        self.settings_path = os.path.abspath(os.path.expanduser("~")
                                             + "/.CanvasSync.settings")

        # Initialize user prompt class, used to get information from the user
        # via the terminal
        self.api = InstructureApi(self)

    def settings_file_exists(self):
        """
        Returns a boolean representing if the settings file
        has already been created on this machine
        """
        return os.path.exists(self.settings_path)

    def is_loaded(self):
        return self.sync_path != "Not set" and \
               self.domain != "Not set" and \
               self.token != "Not set" and \
               self.courses_to_sync[0] != "Not set"

    def load_settings(self, password):
        """
        Loads the current settings from the settings file and sets the
        attributes of the Settings object
        """
        if self.is_loaded():
            return helpers.validate_token(self.domain, self.token)

        if not self.settings_file_exists():
            self.set_settings()
            return True

        encrypted_message = open(self.settings_path, "rb").read()
        messages = decrypt(encrypted_message, password)
        if not messages:
            # Password file did not exist, set new settings
            print(ANSI.format("\n[ERROR] The hashed password file does not"
                              "longer exist. You must re-enter settings.",
                              "announcer"))
            input("\nPres enter to continue.")
            self.set_settings()
            return self.load_settings("")
        else:
            messages = messages.decode("utf-8").split("\n")

        # Set sync path, domain and auth token
        self.sync_path, self.domain, self.token = messages[:3]

        def read_setting(settings_string):
            return settings_string.split("$")[-1] == "True"

        # Extract synchronization settings
        for message in messages:
            if message[:12] == "SYNC COURSE$":
                if self.courses_to_sync[0] == "Not set":
                    self.courses_to_sync.pop(0)
                self.courses_to_sync.append(message.split("$")[-1])

            setting = read_setting(message)
            if message[:6] == "Files$":
                self.modules_settings["Files"] = setting
            if message[:11] == "HTML pages$":
                self.modules_settings["HTML pages"] = setting
            if message[:14] == "External URLs$":
                self.modules_settings["External URLs"] = setting
            if message[:12] == "Assignments$":
                self.sync_assignments = setting
            if message[:13] == "Linked files$":
                self.download_linked = setting
            if message[:17] == "Avoid duplicates$":
                self.avoid_duplicates = setting
            if message[:14] == "Use nicknames$":
                self.use_nicknames = setting

        if not helpers.validate_token(self.domain, self.token):
            return False
        else:
            return True

    def set_settings(self):
        try:
            self._set_settings()
        except KeyboardInterrupt:
            print(ANSI.format("\n\n[*] Setup interrupted, nothing was saved.", formatting="red"))
            sys.exit()

        self.write_settings()

    def _set_settings(self):
        """
        Prompt the user for settings and write the information to a hidden file in the users home directory.
        """

        # Clear the console and print guidance
        self.print_settings(first_time_setup=True, clear=True)

        # Prompt user for sync path
        self.sync_path = user_prompter.ask_for_sync_path()
        self.print_settings(first_time_setup=True, clear=True)

        # Prompt user for domain
        self.domain = user_prompter.ask_for_domain()
        self.print_settings(first_time_setup=True, clear=True)

        # Prompt user for auth token
        self.token = user_prompter.ask_for_token(domain=self.domain)
        self.print_settings(first_time_setup=True, clear=True)

        # Prompt user for course sync selection
        self.courses_to_sync = user_prompter.ask_for_courses(self, api=self.api)
        self.print_settings(first_time_setup=True, clear=True)

        # Ask user for advanced settings
        show_advanced = user_prompter.ask_for_advanced_settings(self)

        if show_advanced:
            self.modules_settings = user_prompter.ask_for_module_settings(self.modules_settings, self)
            self.sync_assignments = user_prompter.ask_for_assignment_sync(self)
            if not self.sync_assignments:
                self.download_linked = False
            else:
                self.download_linked = user_prompter.ask_for_download_linked(self)
            self.avoid_duplicates = user_prompter.ask_for_avoid_duplicates(self)

    def write_settings(self):
        self.print_settings(first_time_setup=False, clear=True)
        self.print_advanced_settings(clear=False)
        print(ANSI.format("\n\nThese settings will be saved", "announcer"))

        # Write password encrypted settings to hidden file in home directory
        with open(self.settings_path, "wb") as out_file:
            settings = self.sync_path + "\n" + self.domain + "\n" + self.token + "\n"

            for course in self.courses_to_sync:
                settings += "SYNC COURSE$" + course + "\n"

            settings += "Files$" + str(self.modules_settings["Files"]) + "\n"
            settings += "HTML pages$" + str(self.modules_settings["HTML pages"]) + "\n"
            settings += "External URLs$" + str(self.modules_settings["External URLs"]) + "\n"
            settings += "Assignments$" + str(self.sync_assignments) + "\n"
            settings += "Linked files$" + str(self.download_linked) + "\n"
            settings += "Avoid duplicates$" + str(self.avoid_duplicates) + "\n"

            out_file.write(encrypt(settings))

    def print_advanced_settings(self, clear=True):
        """
        Print the advanced settings currently in memory.
        Clear the console first if specified by the 'clear' parameter
        """
        if clear:
            helpers.clear_console()

        print(ANSI.format("\nAdvanced settings", "announcer"))

        module_settings_string = ANSI.BOLD + "[*] Sync module items:        \t" + ANSI.ENDC

        count = 0
        for item in self.modules_settings:
            if self.modules_settings[item]:
                d = " & " if count != 0 else ""
                module_settings_string += d + ANSI.BLUE + item + ANSI.ENDC
                count += 1

        if count == 0:
            module_settings_string += ANSI.RED + "False" + ANSI.ENDC

        print(module_settings_string)
        print(ANSI.BOLD + "[*] Sync assignments:         \t" + ANSI.ENDC + (ANSI.GREEN if self.sync_assignments else ANSI.RED) + str(self.sync_assignments) + ANSI.ENDC)
        print(ANSI.BOLD + "[*] Download linked files:    \t" + ANSI.ENDC + (ANSI.GREEN if self.download_linked else ANSI.RED) + str(self.download_linked) + ANSI.ENDC)
        print(ANSI.BOLD + "[*] Avoid item duplicates:    \t" + ANSI.ENDC + (ANSI.GREEN if self.avoid_duplicates else ANSI.RED) + str(self.avoid_duplicates) + ANSI.ENDC)

    def print_settings(self, first_time_setup=True, clear=True):
        """
        Print the settings currently in memory.
        Clear the console first if specified by the 'clear' parameter
        """
        if clear:
            helpers.clear_console()

        if first_time_setup:
            print(ANSI.format("This is a first time setup.\nYou must specify "
                              "at least the following settings"
                              " in order to run CanvasSync:\n", "announcer"))
        else:
            print(ANSI.format("-----------------------------", "file"))
            print(ANSI.format("CanvasSync - Current settings", "file"))
            print(ANSI.format("-----------------------------\n", "file"))
            print(ANSI.format("Standard settings", "announcer"))

        print(ANSI.BOLD + "[*] Sync path:             \t" + ANSI.ENDC + ANSI.BLUE + self.sync_path + ANSI.ENDC)
        print(ANSI.BOLD + "[*] Canvas domain:         \t" + ANSI.ENDC + ANSI.BLUE + self.domain + ANSI.ENDC)
        print(ANSI.BOLD + "[*] Authentication token:  \t" + ANSI.ENDC + ANSI.BLUE + self.token + ANSI.ENDC)

        if len(self.courses_to_sync) != 0:
            if self.courses_to_sync[0] == "Not set":
                d = ""
            else:
                d = "1) "
            print(ANSI.BOLD + "[*] Courses to be synced:  \t%s" % d + ANSI.ENDC + ANSI.BLUE + self.courses_to_sync[0] + ANSI.ENDC)

            for index, course in enumerate(self.courses_to_sync[1:]):
                print(" "*27 + "\t%s) " % (index+2) + ANSI.BLUE + course + ANSI.ENDC)

    def show(self, quit=True):
        """
        Show the current settings
        If quit=True, sys.exit after user confirmation
        """
        valid_token = self.load_settings("")

        self.print_settings(first_time_setup=False, clear=True)
        self.print_advanced_settings(clear=False)

        if not valid_token:
            self.print_auth_token_reset_error()

        if quit:
            sys.exit()
        else:
            input("\nHit enter to continue.")

    def print_auth_token_reset_error(self):
        """
        Prints error message for when the auth token stored in the
        settings is no longer valid
        """
        print("\n\n[ERROR] The authentication token has been reset.\n"
              "        You must generate a new from the canvas webpage and"
              " reset the CanvasSync settings\n"
              "        using the --setup command line arguments or from the"
              " main menu.")

    def show_main_screen(self, settings_file_exists):
        """
        Linker method to the show_main_screen function of the
        user_prompter module
        """
        return user_prompter.show_main_screen(settings_file_exists)
