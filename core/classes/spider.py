from ..util.base import (
    url_remove_query,
    soup_tag_itr,
    async_exec_func_list_itr
)
from .webviewer import WebViewer

class Spider(WebViewer):
    '''
    '''
    def __init__(self, url):
        super().__init__(url)
        self.visited_web = {'/'}

    def has_visited(self, url):
        url = url_remove_query(url)
        return url in self.visited_web

    def add_to_visit(self, url):
        url = url_remove_query(url)
        self.visited_web.add(url)

    def parse_all_href_itr(self, response):
        soup = self._parse_response(response)
        for a in soup_tag_itr(soup, 'a'):
            if a.has_attr('href'):
                yield a['href']
