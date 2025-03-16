"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

synchronizer.py, CanvasEntity class

The Synchronizer class is the highest level CanvasEntity object in the folder hierarchy.
It inherits from the CanvasEntity base class and extends its functionality to allow downloading
information on courses listed in the Canvas system.
A Course object is initialized for each course found and appended to a list of children under the Synchronizer object.
Synchronization, walking and printing of the folder hierarchy starts by invoking the method on the Synchronizer object
which in turn propagates the signal to all children objects.

The Synchronizer encapsulates a list of children Course objects.

"""

# CanvasSync modules
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.course import Course


class Synchronizer(CanvasEntity):
    def __init__(self, settings, api):
        """
        Constructor method, initializes base CanvasEntity class and adds all children
        Course objects to the list of children

        settings : object | A Settings object, has top-level sync path attribute
        api      : object | An InstructureApi object
        """

        if not settings.is_loaded():
            settings.load_settings()

        # Get the corrected top-level sync path
        sync_path = settings.sync_path

        # A dictionary to store lists of CanvasEntity objects
        # added to the hierarchy under a course ID number
        self.entities = {}

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=-1,
                              name="",
                              sync_path=sync_path,
                              api=api,
                              settings=settings,
                              synchronizer=self,
                              identifier="synchronizer")

    def __repr__(self):
        """ String representation, overwriting base class method """
        return "\n[*] Synchronizing to folder: %s\n" % self.sync_path

    def get_entities(self, course_id):
        """ Getter method for the list of Entities """
        return self.entities[course_id]

    def add_entity(self, entity, course_id):
        """ Add method to append CanvasEntity objects to the list of entities """
        self.entities[course_id].append(entity)

    def download_courses(self):
        """ Returns a dictionary of courses from the Canvas server """
        return self.api.get_courses()

    def add_courses(self):
        """
        Method that adds all Course objects representing Canvas courses to the
        list of children
        """
        # Download list of dictionaries representing Canvas crouses and
        # add them all to the list of children
        for course_information in self.download_courses():
            if "course_code" not in course_information:
                continue

            # Add an empty list to the entities dictionary that will
            # store entities when added
            self.entities[course_information["id"]] = []

            # Create Course object
            course = Course(course_information,
                            parent=self,
                            settings=self.settings)
            self.add_child(course)

    def sync(self):
        """
        1) Adding all Courses objects to the list of children
        2) Synchronize all children objects
        """
        self.print(str(self))

        self.add_courses()

        super().sync()
