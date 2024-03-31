import csv
import requests
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


useragents = {"User-Agent" : UserAgent().random}


class Category:
    # Инициализируем атрибуты класса
    def __init__(self, link: str) -> None:
        self.link = link
        self.request = requests.get(link, headers=useragents)
        self.soup = BeautifulSoup(self.request.text, "lxml")


    # Приватный метод для обращения к другим ссылкам
    async def __any_soup(self, url) -> BeautifulSoup:
        request = requests.get(url, headers=useragents)
        return BeautifulSoup(request.text, "lxml")


    # Проверяем ссылку на валидность и доступность
    async def is_valid_link(self) -> bool:
        if "https://online.metro-cc.ru/category/" in self.link and self.request.ok:
            return True
        else:
            return False


    # Получаем информацию о категории - Имя, Кол-во товаров
    async def info(self) -> list:
        category_name = self.soup.find(class_="subcategory-or-type__heading-title catalog-heading heading__h1").text
        category_quantity = self.soup.find(class_="heading-products-count subcategory-or-type__heading-count").text
        return [category_name.strip(), category_quantity.strip()]
    

    # Получаем кол-во страниц в категории
    async def __page_quantity(self) -> int:
        all_elements = self.soup.find(class_="catalog-paginate v-pagination")
        quantity = all_elements.find_all("li")[-2]
        return int(quantity.text)


    # Получаем ссылки на все страницы категории
    async def all_general_pages(self) -> list:
        pages = []
        for page_num in range(1, await self.__page_quantity()):
            pages.append(self.link + f"?page={str(page_num)}")
        return pages


    # Получаем карточки товаров с переданной страницы
    async def all_products_card(self, general_page_link: str) -> list:
        all_products_card = []
        soup = await self.__any_soup(general_page_link)
        page_cards = soup.find_all(class_="catalog-2-level-product-card product-card subcategory-or-type__products-item with-prices-drop")
        for card in page_cards:
            all_products_card.append(card)
        return all_products_card
    

    # Получаем информацию о товаре из переданной карточки
    async def product_info(self, product_card: list) -> tuple:
        id = product_card.get("id")
        name = product_card.find(class_="product-card-name__text").text
        link = "https://online.metro-cc.ru" + product_card.find(class_="product-card-photo__link reset-link").get("href")
        amount = product_card.find(class_="product-price__sum-rubles").text
        sale_amount = product_card.find_all(class_="product-price__sum-rubles")[-1].text
        brand_page_soup = await self.__any_soup(link)
        brand = brand_page_soup.find_all(class_="product-attributes__list-item")[6].find("a").text
        return (id, name.strip(), link, f"{amount.strip()} rub", f"{sale_amount.strip()} rub", brand.strip())


async def csv_writer(filename: str, info_tuple: str) -> None:
    with open(filename, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(info_tuple)


async def main() -> None:
    url = Category(input("[+] Введите ссылку на категорию товара на сайте https://online.metro-cc.ru/: "))

    # Проверяем ссылку на валидность
    try:
        if not await url.is_valid_link():
            print("[-] Что то не так с ссылкой или сайт не доступен!")
            print(f"[-] Статус код ответа сайта - {url.request.status_code}")
            exit()
        else:
            pass
    except Exception as check_available_error:
        print(f"[-] Произошла ошибка при проверке доступности сайта!\nОшибка: {check_available_error}")

    # Выводим пользователю информацию о категории
    try:
        category_info = await url.info()
        print(f"[+] Обнаруженых товаров в категории {category_info[0]}: {category_info[1]}!")
        print("[+] Внимание: не всегда все из представленных товаров доступны для покупки!")
        print("[+] Парсер парсит только доступные для покупки товары!")
        print("[+] Начинаю парсинг карточек товаров...")
        link_counter = 0; card_counter = 0
    except Exception as start_error:
        print(f"[-] Произошла ошибка при попытке начать парсинг!\nОшибка: {start_error}")

    # Создаём csv-файл с заголовками
    filename = f"{url.link[35:].split('/')[-1]}_{str(datetime.now().date())}.csv"
    with open(filename, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(("id", "name", "link", "amount", "sale_amount", "brand"))

    # Начинаем парсить продукты со страниц
    try:
        for link in await url.all_general_pages():
            link_counter += 1
            for card in await url.all_products_card(link):
                card_counter += 1
                await csv_writer(filename, await url.product_info(card))
    except Exception as progress_error:
        print(f"[-] Произошла ошибка при парсинге!\nОшибка: {progress_error}")

    # Информируем о завершении работы скрипта
    print(f"[+] Товаров распаршено - {card_counter}!")
    print(f"[+] Страниц распаршено - {link_counter}!")
    print(f"[+] Готовый csv-файл сохранён под названием - {filename}!")


if __name__ == "__main__":
    asyncio.run(main())
