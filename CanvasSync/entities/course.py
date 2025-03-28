"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

course.py, Second level class in hierarchy

The Course class is the second level CanvasEntity object in the folder hierarchy. It inherits from the base CanvasEntity
class and extends its functionality to allow downloading information on Modules listed under the course in the Canvas
system. A Module object is initialized for each module found and appended to a list of children under the
Course object. In addition, the object may initialize and store the AssignemntsFolder object representing the collection
of assignments of the course as well as a single Folder object representing the collection of Folders and Files stored
under the 'Files' section in Canvas.

The Synchronizer class is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# CanvasSync modules
import os

from CanvasSync.entities.assignments_folder import AssignmentsFolder
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.folder import Folder
from CanvasSync.entities.isolated_page import IsolatedPage
from CanvasSync.entities.module import Module
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Course(CanvasEntity):
    def __init__(self, course_info, parent, settings):
        """
        Constructor method, initializes base CanvasEntity class and adds all children Module objects to the list of children

        course_info   : dict    | A dictionary of information on the Canvas course object
        parent        : object  | The parent object, the Synchronizer object
        """

        self.course_info = course_info

        course_id = self.course_info["id"]

        course_name = helpers.get_corrected_name(self.course_info["course_code"].split(";")[-1])

        if settings.use_nicknames:
            course_name = self.course_info["name"]

        course_path = os.path.join(parent.get_path(), course_name)

        self.to_be_synced = True if course_name in parent.settings.courses_to_sync else False

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=course_id,
                              name=course_name,
                              sync_path=course_path,
                              parent=parent,
                              identifier="course",
                              folder=self.to_be_synced)

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format("[SYNCED]" if self.to_be_synced else "[SKIPPED]", formatting="green" if self.to_be_synced else "yellow")
        return status + " " * (7 if self.to_be_synced else 6) + "|   " + "\t" * self.indent + "%s: %s" \
                                                        % (ANSI.format("Course", formatting="course"), self.name)

    def download_modules(self):
        """ Returns a list of dictionaries representing module objects """
        return self.api.get_modules_in_course(self.id)

    def add_modules(self):
        """ [HIDDEN]  Method that adds all Module objects to the list of Module objects """

        # Download list of dictionaries representing modules and add them all to the list of children
        modules = self.download_modules()
        # Sort modules by id
        modules = sorted(modules, key=lambda m: m['id'])
        for position, module_info in enumerate(modules):
            module = Module(module_info, position+1, parent=self)
            self.add_child(module)

    def download_assignments(self):
        """ Return a list of dictionaries representing assignment objects """
        return self.api.get_assignments_in_course(self.id)

    def add_assignments_folder(self):
        """ Add an AssigmentsFolder object to the children list """

        # Download potential assignments
        assignments_info_list = self.download_assignments()

        if len(assignments_info_list) == 0:
            return

        assignments = AssignmentsFolder(assignments_info_list, self)
        self.add_child(assignments)

    def add_files_folder(self):
        """ Add a SubFolder object representing the files folder of the course """

        # The main file folder should always be the first in the list, but is there a better way to get this initial ID
        # than downloading the entire list of folders??
        folders = self.api.get_folders_in_course(self.id)

        main_folder = None
        for folder in folders:
            if folder["full_name"] == "course files":
                main_folder = folder
                break

        # Change name of folder
        main_folder["name"] = "Files"

        folder = Folder(main_folder, self)
        self.add_child(folder)
    
    def download_pages(self):
        """ Return a list of dictionaries representing page objects """
        return self.api.get_pages_in_course(self.id)

    def add_pages(self):
        """ Add all Page objects to the children list """
        pages_path = os.path.join(self.get_path(), "Pages")
        pages = self.download_pages()
        if pages:
            os.makedirs(pages_path, exist_ok=True)

        for page_info in pages:
            page = IsolatedPage(page_info, self.id, pages_path, self)
            self.add_child(page)

    def sync(self):
        """
        1) Adding all Modules and AssignmentFolder objects to the list of children
        2) Synchronize all children objects
        """
        self.print(str(self))

        if not self.to_be_synced:
            # Print without adding any children
            super().sync()
            return

        if not list(self.settings.modules_settings.values()) == [False, False, False]:
            self.add_modules()
            self.add_pages()

        if self.settings.sync_assignments:
            # Add an AssignmentsFolder if at least one assignment is found under the course
            self.add_assignments_folder()

        # Add Various Files folder
        self.add_files_folder()

        super().sync()
