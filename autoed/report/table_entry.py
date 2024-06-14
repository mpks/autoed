"""Here we define different table entry clases for the HTML report"""


class PipelineEntry:

    def __init__(self, title='default', success=None,
                 warnings=None, link=None, tooltip=None):
        """A class to keep pipeline processing summary data"""
        self.title = title
        self.success = success
        self.warnings = warnings
        self.tooltip = tooltip
        self.link = link

    def to_dict(self):
        out = {}
        out['title'] = self.title
        out['success'] = self.success
        self['warnings'] = self.warnings
        self['tooltip'] = self.tooltip
        self['link'] = self.link
