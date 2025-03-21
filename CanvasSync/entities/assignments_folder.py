"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

assignments_folder.py, entity Class

The AssignmentsFolder class is a simple container class storing a list of child Assignment objects.
It is one level below the parent Course class and inherits from the CanvasEntity base class.

A Course object is the parent object.

See developer_info.txt file for more information on the class hierarchy of entity objects.

"""

# CanvasSync module imports
import os

from CanvasSync.entities.assignment import Assignment
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.utilities.ANSI import ANSI


class AssignmentsFolder(CanvasEntity):
    def __init__(self, assignments_info, parent):
        """
        Constructor method, initializes base CanvasEntity class

        assignments_info : dict   | A list of dictionaries of information on all Canvas assignments object under a course
        parent           : object | The parent object, a Course object
        """

        self.assignments_info = assignments_info

        # Initialize entity with hardcoded ID and name, we always want the folder to be named "Assignments"
        assignments_folder_id = -1
        assignments_folder_name = "Assignments"
        assignments_folder_path = os.path.join(parent.get_path(), assignments_folder_name)

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=assignments_folder_id,
                              name=assignments_folder_name,
                              sync_path=assignments_folder_path,
                              parent=parent,
                              identifier="assignment_folder")

    def __repr__(self):
        """ String representation, overwriting base class method """
        status = ANSI.format("[SYNCED]", formatting="green")
        return status + " " * 7 + "|   " + "\t" * self.indent + "%s: %s" \
                                                                   % (ANSI.format("Assignments Folder",
                                                                                  formatting="assignments"),
                                                                      self.name)

    def add_assignments(self):
        """ Add an Assignment object to the list of children """

        for assignment_info in self.assignments_info:
            assignment = Assignment(assignment_info, self)
            self.add_child(assignment)

    def sync(self):
        """
        1) Adding all Assignment objects to the list of children
        2) Synchronize all children objects
        """
        self.print(str(self))

        self.add_assignments()

        super().sync()
