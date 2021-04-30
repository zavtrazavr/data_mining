from pathlib import Path
import requests
import bs4
from urllib.parse import urljoin
import locale
import datetime
import re
import pymongo


class MagnitParser:

    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

    def __init__(self, shop_url, start_url, db_client):
        self.shop_url = shop_url
        self.start_url = start_url
        self.db = db_client["gb_data_mining_15_02_2021"]
        self.collection = self.db["magnit_products"]

    def _get_response(self, url):
        return requests.get(url)

    def _get_soup(self, url):
        response = self._get_response(url)
        return bs4.BeautifulSoup(response.text, 'lxml')

    def get_date(self, str_date: str):
        digit_index = re.search(r'\d{2}\s\w{3}', str_date)
        if digit_index:
            date = f'{digit_index[0]} {datetime.datetime.now().year}'
            datetime_result = datetime.datetime.strptime(date, u'%d %b %Y')
            return datetime_result
        else:
            pass

    def run(self):
        soup = self._get_soup(self.start_url)
        catalog = soup.find('div', attrs={'class': 'сatalogue__main'})
        #print(catalog)
        for prod_a in catalog.find_all('a', recursive=False):
            product_data = self._parse(prod_a)
            self._save(product_data)


    def get_template(self):
        return({
            'url': lambda a: urljoin(self.start_url, a.attrs.get('href')),
            'promo_name': lambda a: a.find('div', attrs={'class': 'card_sale__name'}).text,
            'product_name': lambda a: a.find('div', attrs={'class': 'card-sale__title'}).text,
            'old_price': lambda a: f"{(a.find('div', attrs={'class': 'label__price label__price_old'})) .find('span', {'class': 'label__price-integer'}).text}." \
                                    f"{(a.find('div', attrs={'class': 'label__price label__price_old'})).find('span', {'class': 'label__price-decimal'}).text}",
            'new_price': lambda a: f"{(a.find('div', attrs={'class': 'label__price_new'})).find('span', {'class': 'label__price-integer'}).text}." \
                                    f"{(a.find('div', attrs={'class': 'label__price_new'})).find('span', {'class': 'label__price-decimal'}).text}",
            'image_url': lambda a: urljoin(self.shop_url, (a.find('div', {'class': 'card-sale__col card-sale__col_img'})).find('source')['data-srcset']),
            'date_from': lambda a: self.get_date((a.find('div', attrs={'class': "card-sale__date"})).find('p').text),
            'date_to': lambda a: self.get_date((a.find('div', attrs={'class': "card-sale__date"})).find('p').find_next_sibling('p').text)
        })

    def _parse(self, product_a):
        data = {}
        for key, funk in self.get_template().items():
            try:
                data[key] = funk(product_a)
            except AttributeError:
                pass
        return data

    def _save(self, data: dict):
        self.collection.insert_one(data)


def get_save_path(dir_name):
    dir_path = Path(__file__).parent.joinpath(dir_name)
    if not dir_path.exists():
        dir_path.mkdir()
    return dir_path


if __name__ == "__main__":
    url = "https://magnit.ru/promo/"
    shop_url = 'https://magnit.ru'
    save_path = get_save_path("magnit_product")
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    parser = MagnitParser(shop_url, url, db_client)
    parser.run()