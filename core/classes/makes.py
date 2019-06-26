from .webviewer import WebViewer
from ..util.base import (
    BASEDIR,
    soup_tag_itr,
    soup_find_tag,
)
import os
import json

class Makes(WebViewer):
    '''
    '''
    def __init__(self):
        make_url = 'http://www.autotrader.ca'
        super().__init__(make_url)
        self.make_file_name = 'makes.txt'

    def load_makes(self, data_size_threshold=0):
        if not data_size_threshold:
            data_size_threshold = 1000
            must_from_web = False
        else:
            must_from_web = True
        make_file_path = os.path.join(BASEDIR, self.make_file_name)
        makes = dict()
        if os.path.exists(os.path.join(BASEDIR, 'makes.txt')) and not must_from_web:
            with open(make_file_path) as f:
                print('load makes from file')
                makes = json.loads(f.read())
        else:
            with open(make_file_path, 'w+') as f:
                print('load makes from web')
                makes = self._load_makes(data_size_threshold)
                f.write(json.dumps(makes))
        return makes

    def _load_makes(self, threshold):
        response = self._load_content(self.url)
        soup = self._parse_response(response)
        target_tag = 'optgroup'
        target_label = 'All Makes'
        tag = soup_find_tag(soup, target_tag, {'label': target_label})
        ret = dict()
        for child in soup_tag_itr(tag, 'option'):
            if child.has_attr('data-count') and int(child['data-count']) > threshold:
                ret[child.string] = int(child['data-count'])
        return ret
