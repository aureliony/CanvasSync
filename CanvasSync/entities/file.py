"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

file, CanvasEntity Class

The File class stores information on files hosted on the Canvas server. It represents an end point in the hierarchy and
contains no child objects. When the sync method is invoked the file will be downloaded or skipped depending on if it is
already present in at the sync path.

A Module, SubHeader, Folder or Assignment object is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# Inbuilt modules
import os
from datetime import datetime

from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class File(CanvasEntity):
    def __init__(self, file_info, parent, add_to_list_of_entities=True):
        """
        Constructor method, initializes base CanvasEntity class

        assignment_info : dict   | A dictionary of information on the Canvas file object
        parent          : object | The parent object, a Module, SubHeader, Folder or Assignment object
        """

        self.file_info = file_info

        self.locked = self.file_info["locked_for_user"]

        file_id = self.file_info[u"id"]
        file_name = helpers.get_corrected_name(self.file_info[u"display_name"])
        file_path = os.path.join(parent.get_path(), file_name)

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=file_id,
                              name=file_name,
                              sync_path=file_path,
                              parent=parent,
                              folder=False,
                              identifier=u"file",
                              add_to_list_of_entities=add_to_list_of_entities)

    def __repr__(self):
        """ String representation, overwriting base class method """
        return u" " * 15 + u"|   " + u"\t" * self.indent + u"%s: %s" % (ANSI.format(u"File",
                                                                                    formatting=u"file"),
                                                                        self.name)

    def download(self):
        """ Download the file """
        server_time_modified = datetime.strptime(self.file_info["modified_at"], "%Y-%m-%dT%H:%M:%SZ")

        if os.path.exists(self.sync_path):
            local_time_modified = datetime.fromtimestamp(os.path.getmtime(self.sync_path)) \
                                                    .replace(microsecond=0) # Remove milliseconds as Canvas API only returns seconds

            if server_time_modified <= local_time_modified:
                # local file is up-to-date
                return False

            # delete the local outdated file
            os.remove(self.sync_path)

        self.print_status(u"DOWNLOADING", color=u"blue")

        # Download file payload from server
        file_data = self.api.download_file_payload(self.file_info[u"url"])

        # Write data to file
        try:
            with open(self.sync_path, u"wb") as out_file:
                out_file.write(file_data)

            # Set the accessed and modified time to the same as the server file
            modtime = server_time_modified.timestamp()
            os.utime(self.sync_path, times=(modtime, modtime))

        except KeyboardInterrupt as e:
            # If interrupted mid-writing, delete the corrupted file
            if os.path.exists(self.sync_path):
                os.remove(self.sync_path)

            # Re-raise, will be catched in CanvasSync.py
            raise e

        return True

    def sync(self):
        """
        Synchronize the file by downloading it from the Canvas server and saving it to the sync path
        If the file has already been downloaded, skip downloading.
        File objects have no children objects and represents an end point of a folder traverse.
        """
        if not self.locked:
            self.download()
            self.print_status(u"SYNCED", color=u"green")

        else:
            self.print_status(u"LOCKED", color=u"red")

        super().sync()
