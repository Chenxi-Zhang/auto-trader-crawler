from core.classes.carspider import (
    CarSpiderMultiThread,
    CarSpider,
)
from core.classes.makes import Makes

if __name__ == "__main__":
    maker = Makes()
    make = maker.load_makes(1)
    for brand, num in make.items():
        spider = CarSpider(brand, num)
        c = CarSpiderMultiThread(spider)
        c.go(16)
