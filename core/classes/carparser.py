from .webviewer import WebViewer
from ..util.base import (
    soup_find_tag,
    soup_tag_itr,
)

class CarParser(WebViewer):
    '''
    '''
    def __init__(self, url):
        super().__init__(url)
        self.info = None

    def load_car_info(self):
        if not self.is_content_loaded:
            self.load_content()
        return self

    def parse_car_info(self, *arg):
        if not self.is_content_parsed:
            self.parse_response()
        return self

    def is_car_page(self, soup=None):
        if not soup:
            if not self.is_content_parsed:
                self.load_car_info()
            if not self.is_content_loaded:
                self.parse_car_info()
            soup = self.soup
            self.soup = None
        spec_t = soup_find_tag(soup, 'div', {'id': 'vdp-specs-content'})
        price = soup_find_tag(soup, 'h2', {'class': 'vdp-hero-price'})
        year = soup_find_tag(soup, 'meta', {'content': 3}).find_next('span', {'itemprop': 'name'})
        if not spec_t:
            print('not a car page')
            return None
        print('parsing car')
        res = dict()
        res['PRICE'] = price.string.strip() if price else 0
        res['YEAR'] = year.string if year else 0
        th = soup_tag_itr(spec_t, 'th')
        td = soup_tag_itr(spec_t, 'td')
        for h in th:
            d = next(td)
            res[h.string] = d.string
        self.info = res
        return res

    def __str__(self):
        return self.info
