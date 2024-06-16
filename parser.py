from urllib.request import urlopen
#Файл с синхронным парсером, функции здесь не асинхронные, тут собираем данные "статично" с одного сайта
import requests
from bs4 import BeautifulSoup
from urllib.error import URLError, HTTPError
import settings
import asyncio
import aiohttp
from models import db_session, Kirpich

# Ссылка на магазин, который парсим
ROOT = 'https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai/'#Главная страница
CATEG_ROOT = 'https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai'
ITEMS_ROOT = "https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai/catalog/stroymaterialy/"#Ссылка для теста парсера на одной странице с строй материалами
def get_first_text(iter):
    for item in iter:
        return item.text.strip()

# Получаем html страницы
def fetcher():
    with urlopen(ITEMS_ROOT) as request:
        return request.read()

# Парсим страницу
# Парсим Категории получаем ссылки на них
def CategoryParser(html):
    urls = []
    soup = BeautifulSoup(html, features="lxml")
    for i, div in enumerate(soup.select('ul.catalog-menu__main-list li')):
        Category = div.find('a',class_="catalog-menu__main-list-item")
        Category_name = Category.get_text(strip=True)
        url_element = Category.get('href')  # Получаем список элементов <a>
        urls.append(CATEG_ROOT + url_element)
    return urls

#Нужно запарсить название, артикул, описание, цена
def ItemsParser(html):
    soup = BeautifulSoup(html, features='lxml')
    for div in soup.select('ul.category-page__items-list a.product-card__link'):
        code = div.find('p', class_='product-card__info').text.strip()
        ItemRef = div.get('href')
        title= div.find('span', class_='product-card__title').text.strip()
        price = div.find('p', class_='product-card__price').text.strip()
        description_html = CATEG_ROOT+ItemRef
        print(description_html)
        soup_descrip = BeautifulSoup(urlopen(description_html).read(), features='lxml')
        contents = soup_descrip.find('div', class_='product-page__details-text collapsed')
        if contents:
                description = contents.find('p').text.strip()
        else:
                description = "Details section not found"
        print(title,code,price,description)

        #db_session.add(item)
        #db_session.commit()

if __name__ == '__main__':

    print(ItemsParser(fetcher()))