"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

assignment.py, CanvasEntity Class

The Assignment class stores a list of child File objects and creates HTML
pages representing the assignment description.

It is one level below the parent container AssignmentsFolder class and
inherits from the CanvasEntity base class.

An AssignmentsFolder object is the parent object.

See developer_info.txt file for more information on the class hierarchy
of entity objects.
"""

# Inbuilt modules
import os
import re

# CanvasSync module imports
from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.file import File
from CanvasSync.entities.linked_file import LinkedFile
from CanvasSync.entities.page import Page
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Assignment(CanvasEntity):
    def __init__(self, assignment_info, parent):
        """
        Constructor method, initializes base CanvasEntity class

        assignment_info : dict   | A dictionary of information on the Canvas assignment object
        parent          : object | The parent object, an AssignmentsFolder object
        """

        self.assignment_info = assignment_info
        assignment_id = self.assignment_info[u"id"]
        assignment_name = helpers.get_corrected_name(assignment_info[u"name"])
        assignment_path = os.path.join(parent.get_path(), assignment_name)

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=assignment_id,
                              name=assignment_name,
                              sync_path=assignment_path,
                              parent=parent,
                              identifier=u"assignment")

    def __repr__(self):
        """ String representation, overwriting base class method """
        return u" " * 15 + u"|   " + u"\t" * self.indent + u"%s: %s" \
                                                                   % (ANSI.format(u"Assignment", formatting=u"assignment"),
                                                                      self.name)

    def make_html(self):
        """ Create the main HTML description page of the assignment """
        # Create URL pointing to Canvas live version of the assignment
        body = self.assignment_info.pop(u"description") or u"No description"
        output_path = os.path.join(self.sync_path, self.name + u".html")
        helpers.make_html(
            self.name,
            body,
            self.assignment_info,
            output_path,
            self.print_status
        )


    def add_files(self):
        """
        Add all files that can be found in the description of the
        assignment to the list of children and sync
        """
        # Get file URLs pointing to Canvas items
        try:
            canvas_file_urls = re.findall(r'data-api-endpoint=\"(.*?)\"',
                                          self.assignment_info.get(u"description") or u"")
        except:
            canvas_file_urls = []

        # Download information on all found files and add File objects
        # to the children
        for url in canvas_file_urls:
            file_info = self.api.download_item_information(url)

            if u'display_name' in file_info:
                item = File(file_info, parent=self)
            elif u'page_id' in file_info:
                item = Page(file_info, parent=self)
            else:
                # Unknown entity, skip it
                item = None
            if item:
                self.add_child(item)

        if self.settings.download_linked:
            # We also look for links to files downloaded from other servers
            # Get all URLs ending in a file name (determined as a ending with
            # a '.' and then between 1 and 10 of any characters after that).
            # This has 2 purposes:
            # 1) We do not try to re-download Canvas server files, since
            #    they are not matched by this regex
            # 2) We should stay clear of all links to web-sites
            #    (they could be large to download, we skip them here)
            urls = re.findall(r'href=\"([^ ]*[.]{1}.{1,10})\"',
                              self.assignment_info.get(u"description") or u"")

            for url in urls:
                linked_file = LinkedFile(url, parent=self)
                if linked_file.url_is_valid():
                    self.add_child(linked_file)
                else:
                    del linked_file

    def sync(self):
        """
        1) Adding all File and LinkedFile objects to the list of children
        2) Synchronize all children objects
        """
        self.add_files()
        self.make_html()
        self.print_status(u"SYNCED", color=u"green")

        super().sync()
