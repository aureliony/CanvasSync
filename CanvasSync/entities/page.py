"""
CanvasSync by Mathias Perslev
February 2017

--------------------------------------------

page, CanvasEntity Class

The Page class stores information on HTML pages hosted on the Canvas server. It represents an end point in the hierarchy
and contains no child objects. When the sync method is invoked the HTML pages will be downloaded or skipped depending on
if it is already present in at the sync path. The HTML page will be appended with the title of the page along with a
URL pointing to the live version of the HTML page on the server.

A Module or SubHeader object is the parent object.

See developer_info.txt file for more information on the class hierarchy of CanvasEntities objects.

"""

import os
import re

from json2html import json2html

from CanvasSync.entities.canvas_entity import CanvasEntity
from CanvasSync.entities.file import File
from CanvasSync.entities.linked_file import LinkedFile
from CanvasSync.utilities import helpers
from CanvasSync.utilities.ANSI import ANSI


class Page(CanvasEntity):
    def __init__(self, page_info, parent):
        """
        Constructor method, initializes base CanvasEntity class

        page_info : dict   | A dictionary of information on the Canvas page object
        parent    : object | The parent object, a Module or SubHeader object
        """

        # Sometimes the Page object is initialized with a json dict of information on the file like object representing
        # the HTML page instead of an object on the page itself. This file like object does not store the actual HTML
        # body, which will be downloaded in the self.download() method. The slightly messy code below makes the class
        # functional with either information supplied.
        self.page_item_info = page_info
        self.page_info = self.page_item_info if u"id" not in self.page_item_info else None

        page_id = self.page_item_info[u"id"] if not self.page_info else self.page_info[u"page_id"]
        page_name = helpers.get_corrected_name(self.page_item_info[u"title"])
        page_path = parent.get_path()

        # Initialize base class
        CanvasEntity.__init__(self,
                              id_number=page_id,
                              name=page_name,
                              sync_path=page_path,
                              parent=parent,
                              folder=False,
                              identifier=u"page")

    def __repr__(self):
        """ String representation, overwriting base class method """
        return u" " * 15 + u"|   " + u"\t" * self.indent + u"%s: %s" % (ANSI.format(u"Page",
                                                                                    formatting=u"page"),
                                                                        self.name)

    def download_linked_files(self, html_body):
        sub_files = False

        # Look for files in the HTML body
        # Get file URLs pointing to Canvas items
        canvas_file_urls = re.findall(r'data-api-endpoint=\"(.*?)\"', html_body or "")

        # Download information on all found files and add File objects to the children
        for url in canvas_file_urls:
            try:
                file_info = self.api.download_item_information(url)
                if u'display_name' not in file_info:
                    continue
            except Exception:
                continue

            item = File(file_info, parent=self)
            self.add_child(item)
            sub_files = True

        if self.settings.download_linked:
            # We also look for links to files downloaded from other servers
            # Get all URLs ending in a file name (determined as a ending with a '.'
            # and then between 1 and 10 of any characters after that). This has 2 purposes:
            # 1) We do not try to re-download Canvas server files, since they are not matched by this regex
            # 2) We should stay clear of all links to web-sites (they could be large to download, we skip them here)
            urls = re.findall(r'href=\"([^ ]*[.]{1}.{1,10})\"', html_body or "")

            for url in urls:
                linked_file = LinkedFile(url, self)

                if linked_file.url_is_valid():
                    self.add_child(linked_file)
                    sub_files = True
                else:
                    del linked_file

        return sub_files

    def download(self):
        """ Download the page """
        # Download additional info and HTML body of the Page object if not already supplied
        page_info = self.api.download_item_information(self.page_item_info[u"url"]) if not self.page_info else self.page_info
        # Cache the downloaded data
        self.page_info = page_info.copy()

        # Create a HTML page locally and add a link leading to the live version
        body = page_info.pop(u"body", "")
        html_url = self.page_info.get(u"html_url", "")

        if self.download_linked_files(body):
            # There are linked files, make the html in a new folder
            self.sync_path = os.path.join(self.sync_path, self.name)
            self._make_folder()

        output_path = os.path.join(self.sync_path, self.name + ".html")

        new_content = (
            u"<h1><strong>%s</strong></h1>" % self.name
            + u"<big><a href=\"%s\">Click here to open the live page in Canvas</a></big>" % html_url
            + u"<hr>"
            + (body or u"")
            + (u"<hr>" if body else "")
            + json2html.convert(json=page_info) # Add the page metadata as a table
        )

        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as existing_file:
                old_content = existing_file.read()
        else:
            old_content = None

        if old_content != new_content:
            self.print_status(u"DOWNLOADING", color=u"blue")
            with open(output_path, "w", encoding="utf-8") as out_file:
                out_file.write(new_content)

        return True

    def sync(self):
        """
        Synchronize the page by downloading it from the Canvas server and saving it to the sync path
        If the page has already been downloaded, skip downloading.
        Page objects have no children objects and represents an end point of a folder traverse.
        """
        if self.download():
            self.print_status(u"SYNCED", color=u"green")
        
        for file in self:
            file.update_path()

        super().sync()
