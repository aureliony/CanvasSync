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
from CanvasSync.entities.page import Page
from CanvasSync.utilities.ANSI import ANSI


class IsolatedPage(Page):
    def __init__(self, page_info, course_id, sync_path, parent):
        """
        Constructor method, initializes base CanvasEntity class

        page_info : dict   | A dictionary of information on the Canvas page object
        parent    : object | The parent object, a Module or SubHeader object
        """
        super().__init__(page_info, parent)
        self.course_id = course_id
        self.sync_path = sync_path

    def __repr__(self):
        """ String representation, overwriting base class method """
        return " " * 15 + "|   " + "\t" * self.indent + "%s: %s" % (ANSI.format("Isolated Page",
                                                                                    formatting="page"),
                                                                        self.name)

    def download(self):
        """ Download the page """
        self.page_info = self.api.download_page_information(self.course_id, self.id)
        return super().download()
