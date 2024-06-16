import asyncio
from urllib.request import urlopen

import aiohttp
from bs4 import BeautifulSoup
from urllib.error import URLError
from models import db_session
import time  # Импортируем модуль для измерения времени выполнения

# URL корневой страницы и каталога товаров
ROOT = 'https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai/'#Главная страница
CATEG_ROOT = 'https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai'
ITEMS_ROOT = "https://xn--b1aigedeu0a.xn--90afqsbambik.xn--p1ai/catalog/stroymaterialy/"#Ссылка для теста парсера на одной странице с строй материалами

# Максимальное количество одновременных задач
PARALLEL_TASKS = 90
# Ограничение на количества одновременных запросов
MAX_DOWNLOAD_AT_TIME = asyncio.Semaphore(PARALLEL_TASKS)
#Получаем из объект текст(название или содержимое)
def get_first_text(iter):
    for item in iter:
        return item.text.strip()


#Ф-я получения html в текст
async def fetcher(session, url):
    #Сделали ограничение на максимальное кол-во загрузок одновременно
    async with MAX_DOWNLOAD_AT_TIME:
        try:#То есть здесь подгружаем по максимальному кол-ву страниц, которые можно загрузить параллельно
            async with session.get(url) as response:
                if response.status == 200: #Код означает что страница доступна и никаких ограничений нет
                    return await response.text()
                else:
                    print(f"Ошибка получения данных {url}: {response.status}")
                    return None
        except Exception as e:
            return None


# Получаем массив из категорий
#Для удобства теперь делаем просто массив url чтобы лишний раз не обращаться по ключу и тд, обойти работу с словарем
def CategoryParser(session,html):
    urls = []
    soup = BeautifulSoup(html, features="lxml")
    for i, div in enumerate(soup.select('ul.catalog-menu__main-list li')):
        Category = div.find('a', class_="catalog-menu__main-list-item")
        Category_name = Category.get_text(strip=True)
        url_element = Category.get('href')  # Получаем список элементов <a>
        urls.append(CATEG_ROOT + url_element)
    return urls

# Асинхронная функция для парсинга товаров из страницы категории
#В которой мы получаем страницу которую парсим, и по аналогии с синхронной версией проходим по элементам определенного контейнера и собираем данные о товаре
async def Parser(session, url):
    items_url = f"{url}?page=1&per_page=20"#Указываем чтобы он парсил только первую страницу, этот параметр можно менять
    items_html = await fetcher(session, items_url)
    if items_html:
        soup = BeautifulSoup(items_html, features="lxml")
        for div in soup.select('ul.category-page__items-list a.product-card__link'):
            code = div.find('p', class_='product-card__info').text.strip()
            ItemRef = div.get('href')
            title = div.find('span', class_='product-card__title').text.strip()
            price = div.find('p', class_='product-card__price').text.strip()
            description_html = CATEG_ROOT + ItemRef
            print(description_html)
            soup_descrip = BeautifulSoup(urlopen(description_html).read(), features='lxml')
            contents = soup_descrip.find('div', class_='product-page__details-text collapsed')
            if contents:
                description = contents.find('p').text.strip()
            else:
                description = "Details section not found"
            print(title, code, price, description)



async def main():
    # Основная асинхронная функция для сбора данных
    async with aiohttp.ClientSession() as session:
        root_html = await fetcher(session, ROOT)
        if root_html:
            category_urls = CategoryParser(session, root_html)
            tasks = []
            #Проходим по ссылкам категориям и будем добавлять задачи на парсинг каждой страницы из категории
            for url in category_urls:
                #Добавляем задачу на парсинг страницы категории
                tasks.append(Parser(session, url))
            #Ожидаем как отработуют все таски
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())  # Запускаем асинхронную функцию, которая запускает парсинг всех категорий а также страниц