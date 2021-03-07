from pathlib import Path
import requests
import json
import time


class Parser:
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'}

    def __init__(self, categories: str, start_url: str, params: dict, save_path: Path):
        self.categories = categories
        self.start_url = start_url
        self.params = params
        self.save_path = save_path

    def run(self):
        data = {}
        for category in self._get_categories():
            data['name'], data['category'] = category['parent_group_name'], category['parent_group_code']
            data['products'] = self._get_products(self.start_url, category['parent_group_code'])
            category_path = self.save_path.joinpath(f"{data['name']}.json")
            self._save(data, category_path)

    def get_response(self, url, params=None):
        while True:
            response = requests.get(url, params=params, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def _get_categories(self):
        category_data = self.get_response(self.categories)
        category_json = category_data.json()
        for category in category_json:
            yield category

    def _get_products(self, url, category):
        self.params['categories'] = category
        products = []
        is_first_page = True

        while url:
            if is_first_page:
                response = self.get_response(url, self.params)
                is_first_page = False
            else:
                response = self.get_response(url)

            product_data = response.json()

            for product in product_data["results"]:
                products.append(product)

            url = product_data['next']
        return products

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data))


if __name__ == '__main__':
    products_url = 'https://5ka.ru/api/v2/special_offers/'
    categories_url = 'https://5ka.ru/api/v2/categories/'

    query_params = {'store': None,
              'records_per_page': 12,
              'page': 1,
              'categories': None,
              'ordering': None,
              'price_promo__gte': None,
              'price_promo__lte': None,
              'search': None}

    save_path = Path(__file__).parent.joinpath('category_products')
    if not save_path.exists():
        save_path.mkdir()

    parser = Parser(categories_url, products_url, query_params, save_path)
    parser.run()
