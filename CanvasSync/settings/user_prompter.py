"""
CanvasSync by Mathias Perslev
February 2017

---------------------------------------------

user_prompter.py, module

A collection of functions used to prompt the user for settings.

"""

# TODO
# - Comments
# - Make a Y/N function to reduce code redundancy

# Inbuilt modules
import os

# CanvasSync module import
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


def show_main_screen(settings_file_exists):
    """
    Prompt the user for initial choice of action. Does not allow Synchronization before settings file has been set
    """

    choice = -1
    to_do = "quit"
    while choice not in (0, 1, 2, 3, 4):
        helpers.clear_console()

        # Load version string
        import CanvasSync
        version = CanvasSync.__version__

        title = "CanvasSync v"
        pretty_string = "-" * (len(title) + len(version))

        print(ANSI.format("%s\n%s%s\n%s" % (pretty_string, title, version, pretty_string), "file"))

        print(ANSI.format("Automatically synchronize modules, assignments & files located on a Canvas web server.",
                          "announcer"))
        print(ANSI.format("\nWhat would you like to do?", "underline"))
        print("\n\t1) " + ANSI.format("Synchronize my Canvas", "blue"))
        print("\t2) " + ANSI.format("Set new settings", "white"))
        print("\t3) " + ANSI.format("Show current settings", "white"))
        print("\t4) " + ANSI.format("Show help", "white"))
        print("\n\t0) " + ANSI.format("Quit", "yellow"))

        try:
            choice = int(input("\nChoose number: "))
            if choice < 0 or choice > 4:
                continue
        except ValueError:
            continue

        if choice == 1 and not settings_file_exists:
            to_do = "set_settings"
        else:
            to_do = ["quit", "sync", "set_settings", "show_settings", "show_help"][choice]

    return to_do


def ask_for_sync_path():
    """
    Prompt the user for a path to a folder that will be used to synchronize the Canvas page into
    The path should point into a directory along with a sub-folder name of a folder not already existing.
    This folder wll be created using the os module.
    """

    found = False
    # Keep asking until a valid path has been entered by the user
    while not found:
        sync_path = input("\nEnter a relative or absolute path to sync to (~/Desktop/Canvas etc.):\n$ ")

        # Expand tilde if present in the sync_path
        if "~" in sync_path:
            sync_path = sync_path.replace("~", os.path.expanduser("~"))
        sync_path = os.path.abspath(sync_path)

        if not os.path.exists(os.path.split(sync_path)[0]):
            print("\n[ERROR] Base path '%s' does not exist." % os.path.split(sync_path)[0])
        else:
            found = True

    return sync_path


def ask_for_domain():
    """
    Prompt the user for a Canvas domain.

    To ensure that the API calls are made on an encrypted SSL connection the initial 'https://' is pre-specified.
    To ensure that the user input is 1) a valid URL and 2) a URL representing a Canvas web server request is used
    to fetch a resources on the Canvas page. If the GET requests fails the URL was not valid. If the server returns
    a 404 unauthenticated error the domain is very likely to be a Canvas server, if anything else is returned the
    URL points to a correct URL that is not a Canvas server.
    """
    found = False

    # Keep asking until a valid domain has been entered by the user
    while not found:
        domain = "https://" + input("\nEnter the Canvas domain of your institution:\n$ https://")
        found = helpers.validate_domain(domain)

    return domain


def ask_for_token(domain):
    """
    Prompt the user for an authentication token.

    The token must be generated on the Canvas web page when login in under the "Settings" menu.
    To ensure that the entered token is valid, a request GET call is made on a resource that requires authentication
    on the server. If the server responds with the resource the token is valid.
    """
    found = False

    # Keep asking until a valid authentication token has been entered by the user
    while not found:
        token = input("\nEnter authentication token (see 'Setup' section on https://github.com/perslev/CanvasSync for details):\n$ ")
        found = helpers.validate_token(domain, token)

    return token


def ask_for_courses(settings, api):

    courses = api.get_courses()
    courses = [course for course in courses if 'access_restricted_by_date' not in course]

    if settings.use_nicknames:
        courses = [name["name"] for name in courses if "name" in name]
    else:
        courses = [helpers.get_corrected_name(name["course_code"].split(";")[-1]) for name in courses if "course_code" in name]

    choices = [True]*len(courses)

    choice = -1
    while choice != 0:
        settings.print_settings(clear=True)
        print(ANSI.format("\n\nPlease choose which courses you would like CanvasSync to sync for you:\n", "white"))

        print(ANSI.format("Sync this item\tNumber\tCourse Title", "blue"))
        for index, course in enumerate(courses):
            print("%s\t\t[%s]\t%s" % (ANSI.format(str(choices[index]), "green" if choices[index] else "red"),
                                          index+1, courses[index]))
        print("\n\n\t\t[%s]\t%s" % (0, ANSI.format("Confirm selection (at least one course required)", "blue")))
        print("\t\t[%s]\t%s" % (-1, ANSI.format("Select all", "green")))
        print("\t\t[%s]\t%s" % (-2, ANSI.format("Deselect all", "red")))

        try:
            choice = int(input("\nChoose number: "))
            if choice < -2 or choice > len(courses):
                continue
        except ValueError:
            continue

        if choice == 0:
            if sum(choices) == 0:
                choice = -1
                continue
            else:
                break
        elif choice == -1:
            choices = [True] * len(courses)
        elif choice == -2:
            choices = [False] * len(courses)
        else:
            choices[choice-1] = choices[choice-1] is not True

    print(choices)

    return [x for index, x in enumerate(courses) if choices[index]]


def ask_for_advanced_settings(settings):
    choice = -1
    while choice not in (1, 2):
        settings.print_settings(clear=True)

        print(ANSI.format("\n\nAll mandatory settings are set. Do you wish see advanced settings?",
                          "announcer"))

        print(ANSI.format("\n[1]\tShow advanced settings (recommended)", "bold"))
        print(ANSI.format("[2]\tUse default settings", "bold"))

        try:
            choice = int(input("\nChoose number: "))
        except ValueError:
            continue

        if choice == 1:
            return True
        elif choice == 2:
            return False
        else:
            continue


def ask_for_module_settings(module_settings, settings):
    choice = -1
    while choice != 0:
        settings.print_advanced_settings(clear=True)
        print(ANSI.format("\n\nModule settings", "announcer"))
        print(ANSI.format("In Canvas, 'Modules' may contain various items such as files, HTML pages of\n"
                          "exercises or reading material as well as links to external web-pages.\n\n"
                          "Below you may specify, if you would like CanvasSync to avoid syncing some of these items.\n"
                          "OBS: If you chose 'False' to all items, Modules will be skipped all together.", "white"))

        print(ANSI.format("\nSync this item\tNumber\t\tItem", "blue"))

        list_of_keys = list(module_settings.keys())
        for index, item in enumerate(list_of_keys):

            boolean = module_settings[item]

            print("%s\t\t[%s]\t\t%s" % (ANSI.format(str(boolean), "green"
                                        if boolean else "red"),
                                        index+1, item))

        print("\n\t\t[%s]\t\t%s" % (0, ANSI.format("Confirm selection", "blue")))

        try:
            choice = int(input("\nChoose number: "))
            if choice < 0 or choice > len(module_settings):
                continue
        except ValueError:
            continue

        if choice == 0:
            break
        else:
            module_settings[list_of_keys[choice-1]] = module_settings[list_of_keys[choice-1]] is not True

    return module_settings


def ask_for_assignment_sync(settings):
    choice = -1

    while choice not in (1, 2):
        settings.print_advanced_settings(clear=True)
        print(ANSI.format("\n\nAssignments settings", "announcer"))
        print(ANSI.format("Would you like CanvasSync to synchronize assignments?\n\n"
                          "The assignment description will be downloaded as a HTML to be viewed offline\n"
                          "and files hosted on the Canvas server that are described in the assignment\n"
                          "description section will be downloaded to the same folder.\n", "white"))

        print(ANSI.format("1) Sync assignments (default)", "bold"))
        print(ANSI.format("2) Do not sync assignments", "bold"))

        try:
            choice = int(input("\nChoose number: "))
        except ValueError:
            continue

        if choice == 1:
            return True
        elif choice == 2:
            return False
        else:
            continue


def ask_for_download_linked(settings):
    choice = -1

    while choice not in (1, 2):
        settings.print_advanced_settings(clear=True)
        print(ANSI.format("\n\nAssignments settings", "announcer"))
        print(ANSI.format("You have chosen to synchronise assignments. URLs detected in the\n"
                          "description field that point to files on Canvas will be downloaded\n"
                          "to the assignment folder.\n\n"
                          "CanvasSync may also attempt to download linked files that are NOT\n"
                          "hosted on the Canvas server itself. CanvasSync is looking for URLs that\n"
                          "end in a filename to avoid downloading other linked material such as\n"
                          "web-sites. However, be aware that errors could occur.\n"
                          "\nDo you wish to enable this feature?\n", "white"))

        print(ANSI.format("1) Enable linked file downloading (default)", "bold"))
        print(ANSI.format("2) Disable linked file downloading", "bold"))

        try:
            choice = int(input("\nChoose number: "))
        except ValueError:
            continue

        if choice == 1:
            return True
        elif choice == 2:
            return False
        else:
            continue


def ask_for_avoid_duplicates(settings):
    choice = -1

    while choice not in (1, 2):
        settings.print_advanced_settings(clear=True)
        print(ANSI.format("\n\nVarious files settings", "announcer"))
        print(ANSI.format("In addition to synchronizing modules and assignments,\n"
                          "CanvasSync will sync files located under the 'Files'\n"
                          "section in Canvas into a 'Various Files' folder.\n"
                          "Often some of the files stored under 'Files' is mentioned in\n"
                          "modules and assignments and may thus already exist in another\n"
                          "folder after running CanvasSync.\n\n"
                          "Do you want CanvasSync to avoid duplicates by only downloading\n"
                          "files into the 'Various Files' folder, if they are not already\n"
                          "present in one of the modules or assignments folders?\n", "white"))

        print(ANSI.format("1) Yes, avoid duplicates (default)", "bold"))
        print(ANSI.format("2) No, download all files to 'Various files'", "bold"))

        try:
            choice = int(input("\nChoose number: "))
        except ValueError:
            continue

        if choice == 1:
            return True
        elif choice == 2:
            return False
        else:
            continue
