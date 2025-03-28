"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

Implements a class representing files not located on the Canvas server
Initialization of this object thus does not require a info dictionary as is the case for all classes representing true
Canvas entities. Instead, LinkedFile should be initialized with a direct download link.
However, the LinkedFile is derived from the base entity class and the walk, sync and show methods are implemented
and should be used in a similar fashion to other CanvasEntities objects.

An Assignment object is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

# Inbuilt modules
import os

# Third party modules
import requests

# CanvasSync module imports
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.utilities.ANSI import ANSI


class LinkedFile(CanvasEntity):
    def __init__(self, download_url, parent):
        """
        Constructor method, initializes base CanvasEntity class

        download_url    : string | A URL pointing to a file somewhere on the web
        parent          : object | The parent object, an Assignment object
        """

        self.download_url = download_url
        self.valid_url = True

        # Get the potential file name from the URL
        # OBS: We do not correct the name in this class, as we need to use the length of the name to determine
        # if the link is valid.
        file_name = os.path.split(download_url)[-1]

        # File path
        file_path = os.path.join(parent.get_path(), file_name)

        # No file extension or weirdly long filename will not be allowed
        # (this is not strictly necessary as the regex should only match OK URLs)
        if (
            not os.path.splitext(file_name)[-1]
            or len(file_name) > 60
            or download_url.startswith("mailto:")
        ):
            self.valid_url = False

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=-1,
                              name=file_name,
                              sync_path=file_path,
                              parent=parent,
                              folder=False,
                              identifier="linked_file")

    def __repr__(self):
        """ String representation, overwriting base class method """
        return " " * 15 + "|   " + "\t" * self.indent + "%s: %s" % (ANSI.format("Linked File",
                                                                                    formatting="linkedfile"),
                                                                        self.name)

    def url_is_valid(self):
        return self.valid_url

    def download(self):
        """
        Download the file, returns True or False depecting if the file was downloaded or not. Returns -1 if the file
        was attempted downloaded but failed.
        """
        if os.path.exists(self.sync_path):
            return False

        self.print_status("DOWNLOADED", color="blue")

        # Attempt to download the file
        try:
            response = requests.get(self.download_url)

        except requests.exceptions.RequestException:
            # Could not download, catch any request exception
            self.print_status("FAILED", "red")
            return -1

        # Check for OK 200 HTTP response
        if response.status_code != 200:
            self.print_status("FAILED", "red")
            return -1

        # If here, download was successful, write to disk and print status
        open(self.sync_path, "wb").write(response.content)

        return True

    def sync(self):
        """
        Attempt to download a file a the url 'download_url' to the path 'path'/filename while printing
        the status using an indent of print_indent to align with the parent object
        """
        was_downloaded = self.download()

        if was_downloaded != - 1:
            self.print_status("SYNCED", color="green")

        super().sync()
