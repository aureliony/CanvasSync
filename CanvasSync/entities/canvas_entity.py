"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

CanvasEntity.py, Base class

The base class of the CanvasEntities object hierarchy.
This object implements basic functionality shared across all entities in CanvasEntities package.

The CanvasEntity class holds information such as ID numbers, names and absolute sync path and the list of child objects.
It implements various getter-methods used to access information on objects across the CanvasEntities.
In addition, the object is tied to an identifier string representing what derived class it is tied to.
This is used for methods such as 'get_course' that will transverse the CanvasEntities hierarchy to find the top
level course object.

Any CanvasEntity object may be the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""
# Inbuilt modules
import os
import time
from concurrent.futures import ThreadPoolExecutor

# CanvasSync module imports
from CanvasSync.utilities.ANSI import ANSI
from CanvasSync.utilities.instructure_api import InstructureApi


class CanvasEntity(object):
    def __init__(
        self,
        id_number: str,
        name: str,
        sync_path: str,
        parent: 'CanvasEntity' = None,
        folder: bool = True,
        api: InstructureApi = None,
        settings: 'CanvasEntity' = None,
        identifier: str = "",
        synchronizer: 'CanvasEntity' = None,
        add_to_list_of_entities: bool = True
    ):
        """
        Constructor method

        id_number    : string  | The ID number of the entity, e.g. this could be a Module ID number
        name         : string  | The name of the entity, e.g. this could be the name of a Course
        sync_path    : string  | A string representing the path to where the entity is synced to in the local folder
        parent       : object  | An object representing the 'parent' to this CanvasEntity, that is the CanvasEntity one level above
                                 Note that this does not mean parent in regards to inheritance.
        folder       : boolean | A boolean indicating whether this entity is a folder or file
        api          : object  | An CanvasSync InstructureApi object, should be the same object across the hierarchy during
                                 synchronization.
        settings     : object  | A CanvasSync Settings object, should be the same object across the hierarchy during
                                 synchronization.
        identifier   : string  | A string representing what derived class inherited from this instance of CanvasEntity
        synchronizer : object  | The CanvasSync Synchronizer object
        add_to...    : boolean | A boolean value representing if the instance of the CanvasEntity class should be added to the
                                 list of entities that the Synchronizer object stores.
                                 This value is False for items stored in Folder objects as the Synchronizer class
                                 uses the list of entities to make a black list of files that are already stored
                                 across the hierarchy to avoid duplicates when syncing the 'Files' section - items
                                 within this section should not be taken into account when the black list is made.
        """

        # Identifier information
        self.id = id_number

        # Parent object
        self.parent = parent

        # Identifier, could be "course"
        self.identifier = identifier

        # CanvasEntity name
        self.name = name

        # Is this a folder or file?
        self.folder = folder

        # The same InstructureApi object is used across all Entities and so only the top-level Syncronizer object
        # is initialized with the object. All other lower level Entities fetches the object from their parent.
        if api:
            self.api = api
        else:
            self.api = self.get_parent().get_api()

        # Set settings object
        if settings:
            self.settings = settings
        else:
            self.settings = self.get_parent().get_settings()

        # Get the path of the CanvasEntity in the local folder
        self.sync_path = sync_path

        # Child objects, that is Entities that are located below this current level in the folder hierarchy
        # E.g. this list could contain Item objects located under a Module object.
        self.children = []

        # Indent level
        if self.parent:
            self.indent = self.get_parent().indent + 1
        else:
            self.indent = -1

        # If this CanvasEntity is a folder, create it
        if self.folder:
            self._make_folder()

        # Set synchronizer object
        if synchronizer:
            self.synchronizer = synchronizer
        else:
            self.synchronizer = self.get_parent().get_synchronizer()

            if add_to_list_of_entities:
                # Add CanvasEntity to the list in the Synchronizer object
                self.get_synchronizer().add_entity(self, self.get_course().get_id())

        # Initialize list of args to print
        self.print_queue = []
        self.child_to_print = 0
        self.has_printed = False

    def __getitem__(self, item):
        """ Container get-item method can be used to access a specific child object """
        return self.children[item]

    def __iter__(self):
        """ Iterator method yields all Entities contained by this CanvasEntity """
        for child in self.children:
            yield child

    def __repr__(self):
        """ String representation, overwritten in derived class """
        return u"Base object: %s" % self.name

    def __len__(self):
        """ len() method """
        return len(self.children)

    def __nonzero__(self):
        """ Boolean representation method. Always returns True after initialization. """
        return True

    def __bool__(self):
        """ Boolean representation method. Always returns True after initialization. """
        return self.__nonzero__()

    def get_identifier_string(self):
        """ Getter method for the identifier string """
        return self.identifier

    def get_course(self):
        """ Go up one level until the Course object is reached, then return it """

        if self.get_identifier_string() == u"course":
            return self

        parent = self.parent

        while parent.get_identifier_string().lower() != u"course":
            parent = parent.get_parent()

        return parent

    def get_name(self):
        """ Getter method for the name """
        return self.name

    def get_synchronizer(self):
        """ Getter method for the Synchronizer object """
        return self.synchronizer

    def get_id(self):
        """ Getter method for the ID number """
        return self.id

    def get_parent(self):
        """ Getter method for the parent object """
        return self.parent

    def get_api(self):
        """ Getter method for the InstructureApi object """
        return self.api

    def get_settings(self):
        """ Getter method for the Settings object """
        return self.settings

    def get_path(self):
        """ Getter method for the sync path """
        return self.sync_path

    def add_child(self, child):
        """ Add a child object to the list of children """
        self.children.append(child)

    def get_children(self):
        """ Getter method for the list of children """
        return self.children

    def print(self, *args, **kwargs):
        self.print_queue.append((args, kwargs))

    def print_status(self, status: str, color: str):
        """ Print status to console """
        self.print(ANSI.format(u"[%s]" % status, formatting=color) + str(self)[len(status) + 2:])

    def _flush_print_queue(self):
        for args, kwargs in self.print_queue:
            print(*args, flush=True, **kwargs)

        self.has_printed = True
        self.print_queue.clear()

    def sync(self, threaded=True):
        if not threaded:
            for child in self:
                child.sync()

            self._flush_print_queue()

        else:
            executor = ThreadPoolExecutor()
            futures =  [executor.submit(child.sync) for child in self]

            # Wait for our turn to print
            if self.parent is not None:
                while not self.parent.has_printed or \
                    self != self.parent.children[self.parent.child_to_print]:
                    time.sleep(0.01)

            self._flush_print_queue()
            for future in futures:
                future.result() # Propagate exceptions if present

            executor.shutdown() # This blocks until all jobs are done

        if self.parent is not None:
            self.parent.child_to_print += 1

    def update_path(self):
        """ Update the path to the current parents sync path plus the current file name """
        self.sync_path = os.path.join(self.get_parent().get_path(), self.get_name())

    def _make_folder(self):
        """ Create a folder on the sync path if not already present """
        os.makedirs(self.sync_path, exist_ok=True)
