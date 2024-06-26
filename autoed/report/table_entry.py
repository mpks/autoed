"""Here we define different table entry clases for the HTML report"""


class PipelineEntry:

    def __init__(self,
                 title='default',
                 status=None,
                 indexed=None,
                 unit_cell=None,
                 space_group=None,
                 warnings=None,
                 link=None,
                 tooltip=None):
        """A class to keep pipeline processing summary data"""
        self.title = title
        self.status = status
        self.indexed = indexed
        self.unit_cell = unit_cell
        self.space_group = space_group
        self.warnings = warnings
        self.link = link
        self.tooltip = tooltip

    def to_dict(self):
        out = {}
        out['title'] = self.title
        out['status'] = self.status
        out['indexed'] = self.indexed
        out['unit_cell'] = self.unit_cell
        out['space_group'] = self.space_group
        out['warnings'] = self.warnings
        out['tooltip'] = self.tooltip
        out['link'] = self.link
        return out
