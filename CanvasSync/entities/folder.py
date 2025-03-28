"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

folder.py, CanvasEntity Class

The Folder class represents the top level 'Files' section in Canvas or a sub-folder here-off. The object is a container
of other Folder objects as well as Files objects. Recursion is used to map the Folder hierarchy of the 'Files' section.

A Course or Folder object is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# CanvasSync modules
import os

from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.file import File
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Folder(CanvasEntity):
    def __init__(self, folder_info, parent, black_list=False):
        """
        Constructor method, initializes base Module class and adds all children Folder and/or Item objects to
        the list of children

        folder_info     : dict   | A dictionary of information on the Canvas Folder object
        parent          : object | The parent object, a Folder or Course object
        """

        self.folder_info = folder_info

        folder_id = self.folder_info["id"]
        folder_name = helpers.get_corrected_name(self.folder_info["name"])
        folder_path = os.path.join(parent.get_path(), folder_name)

        # Initialize base Module class
        CanvasEntity.__init__(self,
                              id_number=folder_id,
                              name=folder_name,
                              sync_path=folder_path,
                              parent=parent,
                              identifier="folder")

        self.black_list = black_list

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format("[SYNCED]", formatting="green")
        return status + " " * 7 + "|   " + "\t" * self.indent + "%s: %s" \
                                                                   % (ANSI.format("Folder", formatting="folder"),
                                                                      self.name)

    def initialize_black_list(self):
        """
        Some files may have been added to Module or Assignment objects already, so we do not need to store them again
        This method initializes a list of all file names that exist in the hierarchy of the Course object so far
        """

        # Get all entities listed in the Synchronizer object under the course.
        entities = self.get_synchronizer().get_entities(self.get_course().get_id())

        # Get list of names of all the File objects of the entities list
        black_list = [x.get_id() for x in entities if x.get_identifier_string() == "file"]

        return black_list

    def add_files(self):
        """ Add all files stored by this folder to the list of children """
        files = self.api.get_files_in_folder(self.id)

        for file in files:
            # Skip duplicates if this settings is active
            # (otherwise the list will be empty)
            if not file or file["id"] in self.black_list:
                continue

            file = File(file, self, add_to_list_of_entities=False)
            self.add_child(file)

    def add_sub_folders(self):
        """ Add all sub-folders stored by this folder to the list of children """
        folders = self.api.get_folders_in_folder(self.id)

        for folder in folders:
            if folder["name"] == "course_image":
                # Do we really need that course image?
                continue

            folder = Folder(folder, self, black_list=self.black_list)
            self.add_child(folder)

    def sync(self):
        """
        1) Adding all Files and Folder objects to the list of children
        2) Synchronize all children objects
        """
        self.print(str(self))

        # If avoid duplicated setting is active, initialize black list of files found in Modules and
        # Assignments if it was not passed to the object at initialization.
        if not self.black_list and self.settings.avoid_duplicates:
            self.black_list = self.initialize_black_list()
        elif not self.settings.avoid_duplicates:
            self.black_list = []

        self.add_files()
        self.add_sub_folders()

        super().sync()
