"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

module.py, Third level class in hierarchy

The Module class is the third level CanvasEntity object in the folder hierarchy. It inherits from the base CanvasEntity
class and extends its functionality to allow downloading information on Items (files, URLs and HTML pages) as well as
sub-headers, assignments and files located in the 'Files' section in Canvas.

A Course object is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# CanvasSync modules
import os

from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.external_url import ExternalUrl
from CanvasSync.entities.file import File
from CanvasSync.entities.page import Page
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Module(CanvasEntity):
    def __init__(self, module_info, module_position, parent, identifier="module"):
        """, i
        Constructor method, initializes base CanvasEntity class and adds all children Folder and/or Item objects to the
        list of children

        module_info     : dict   | A dictionary of information on the Canvas module object
        module_position : int    | An integer representing the position of the module in the folder (1 for first folder)
        parent          : object | The parent object, a Course object
        """

        self.module_info = module_info

        module_id = self.module_info["id"]
        module_name = helpers.get_corrected_name(self.module_info["name"])
        module_path = os.path.join(parent.get_path(), "%s - %s" % (module_position, module_name))

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=module_id,
                              name=module_name,
                              sync_path=module_path,
                              parent=parent,
                              identifier=identifier)

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format("[SYNCED]", formatting="green")
        return (status + " " * 7 + "|   " + "\t" * self.indent + "%s: %s"
                                                                   % (ANSI.format("Module", formatting="module"),
                                                                      self.name))

    def get_item_information(self):
        """ Returns a dictionary of items from the Canvas server """
        return self.api.get_items_in_module(self.get_course().get_id(), self.id)

    def add_sub_header(self, folder_info, folder_position, folder_items):
        """
        [HIDDEN] Method that adds a Folder object to the list of children

        folder_id       : int    | The ID number of the folder to initialize an Folder object on
        folder_name     : string | The name representation of the folder
        folder_position : int    | An integer representing the position of the folder in the parent folder, such that
                                   the folder listed first in Canvas gets the folder_position '1'.
        folder_items    : dict   | A dictionary of information on items contained by the sub-folder
        """

        # Initialize Folder object and add to list of children, then sync
        from CanvasSync.entities.sub_header import SubHeader

        sub_folder = SubHeader(folder_info, folder_position, parent=self, items=folder_items)
        self.add_child(sub_folder)

    def add_file(self, file_information):
        """
        Method that adds an Item object to the list of children and synchronizes it
        """

        detailed_file_info = self.api.download_item_information(file_information["url"])

        # Initialize Item object and add to list of children
        if detailed_file_info:
            item = File(detailed_file_info, self)
            self.add_child(item)

    def add_page(self, page_information):
        """
        Method that adds a Page object to the list of children and synchronizes it
        """

        # Initialize Page object and add to list of children
        page = Page(page_information, self)
        self.add_child(page)

    def add_url(self, url_information):
        """
        Method that adds an ExternalUrl object to the list of children and synchronizes it
        """

        # Initialize ExternalUrl object and add to list of children
        url = ExternalUrl(url_information, self)
        self.add_child(url)

    def add_items(self, items=None):
        """
        Method that adds all Items under the module to the list of children.
        If the item is a sub-folder it will be added as a Folder object instead.

        items : list | A list of dictionaries of information on items
                       SubFolders inherit from the Module class and use this feature
        """

        # If the Folder was initialized with an items dictionary, skip downloading
        if not items:
            items = self.get_item_information()

        # Determine which items are in the outer-scope (located in the folder represented by this module) and which
        # items are located in sub-folders under this module.
        items_in_this_scope, sub_folders = helpers.reorganize(items)

        # Add all non-sub-folder items to the list of children. Currently, files, HTML pages and URLs are added.
        for item in items_in_this_scope:
            if item["type"] == "File" and self.settings.modules_settings["Files"]:
                self.add_file(item)
            elif item["type"] in ["Page", "Quiz"] and self.settings.modules_settings["HTML pages"]:
                self.add_page(item)
            elif item["type"] == "ExternalUrl" and self.settings.modules_settings["External URLs"]:
                self.add_url(item)

        # Add all sub-folders as Folder objects to the list of children along with the items the folder contain
        for position, folder in enumerate(sub_folders):
            self.add_sub_header(folder[0], position + 1, folder[1:])

    def sync(self):
        """
        1) Adding all File, Page, ExternalLink and SubFolder objects to the list of children
        2) Synchronize all children objects
        """
        self.print(str(self))

        self.add_items()

        super().sync()
