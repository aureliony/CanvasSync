"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

static_function.py, module

A collection of small static helper-functions used in various modules of CanvasSync.

"""

# TODO
# - Improve domain validation check, it is quite limit at this moment
# - (find better solution to sub-folder problem than the reorganize function?)

import os
from typing import Callable

import requests

from json2html import json2html


def reorganize(items):
    """
    Takes a dictionary of items and parses them for sub-folders.

    A list of items located in the outer scope is returned along with a list of containing dictionaries of items
    contained within each potential sub-folder.

    items : list | A list of JSON dictionary objects containing information on Canvas item objects
    """

    # If no items or the resource that was attempted to be accessed does not exists (for instance if a teacher makes
    # a sub-header with no items in it, accessing the file content of the sub-header will make the server respond with
    # and error report). In both cases return empty lists.
    if (isinstance(items, dict) and list(items.keys())[0] == "errors") or len(items) == 0:
        return [], []

    # Create a list that will store all files located in the outer most scope of the hierarchy
    outer_scope_files = []

    # Create a list that will hold sub dictionaries containing information on all files in the sub-folder
    sub_folders = []

    # Counter value used to keep track of how many the index of the current sub-folder that is being reorganized.
    current_sub_folder_index = -1

    # Get the indent level of the outer most scope, should be that of the 0th item in the list, but we check all here.
    try:
        outer_indent = min([items[index]["indent"] for index in range(len(items))])
    except KeyError:
        print(items)

    # Reorganize all items in 'items'
    for item in items:
        # Get the type of item and indent level
        item_type = item["type"]
        item_indent = item["indent"]

        if item_type == "SubHeader":
            # If "SubHeader" the item is a sub-folder, add it to the list of sub-folders
            current_sub_folder_index += 1
            sub_folders.append([item])
        elif item_indent == outer_indent or current_sub_folder_index == -1:
            # If not a folder, is the item in the outer most scope?
            outer_scope_files.append(item)
        else:
            # File is located in a sub-folder
            sub_folders[current_sub_folder_index].append(item)

    return outer_scope_files, sub_folders


def clear_console():
    """ Clears the console on UNIX and Windows """
    os.system('cls' if os.name == 'nt' else 'clear')


def get_corrected_name(name):
    """
    Validates the name of an Entry
    This method may be extended in the feature to include more validations.

    name : string | A string representing the name of an Entry (Module, File etc.)
    """
    from CanvasSync.utilities import CLEAN_CHARS
    name = name.strip(" .")
    for char, replace in CLEAN_CHARS.items():
        name = name.replace(char, replace)
    max_length = 255
    if len(name) > max_length:
        # The name is too long
        base, ext = os.path.splitext(name)
        name = base[:max_length - len(ext)] + ext
    return name


def validate_domain(domain):
    """
    Validate the the specified domain is a valid Canvas domain by
    interpreting the HTTP response
    """
    try:
        response = requests.get(domain + "/api/v1/courses", timeout=5)
        if response.status_code==401:
            # If this response, the server exists and understands
            # the API call but complains that the call was
            # not authenticated - the URL represents a Canvas server
            return True
        else:
            print("\n[ERROR] Not a valid Canvas web server. Wrong domain?")
            return False
    except Exception:
        print("\n[ERROR] Invalid domain.")
        return False


def validate_token(domain, token):
    """
    Validate the auth token in combination with the domain by interpreting the HTTP response. Should be called
    after the validate_domain function to make sure that errors arise from the token.
    """
    if len(token) < 20:
        print("The server did not accept the authentication token.")
        return False

    response = str(requests.get(domain + "/api/v1/courses",
                                headers={'Authorization': "Bearer %s" % token}).text)

    if "Invalid access token" in response:
        print("The server did not accept the authentication token.")
        return False
    else:
        return True

def make_html(
    name: str,
    body: str,
    page_info: dict[str, str],
    output_path: str
) -> bool:
    """
    Create a HTML page locally and add a link leading to the live version
    """
    url = page_info.get("html_url", "")
    new_content = (
        "<h1><strong>%s</strong></h1>" % name
        + "<big><a href=\"%s\">Click here to open the live page in Canvas</a></big>" % url
        + "<hr>"
        + body
        + ("<hr>" if body else "")
        + json2html.convert(json=page_info) # Add the page metadata as a table
    )

    if os.path.exists(output_path):
        old_content = open(output_path, "r", encoding="utf-8").read()
    else:
        old_content = None

    if old_content != new_content:
        open(output_path, "w", encoding="utf-8").write(new_content)
        return True

    return False
