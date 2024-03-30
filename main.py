import csv
import lxml
import requests
import asyncio
from datetime import datetime
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


SOURCE_URL = input("[+] Введите ссылку на категорию товара на сайте https://online.metro-cc.ru/: ")


if "https://online.metro-cc.ru/category/" not in SOURCE_URL:
    print("[-] Некорректный ввод!\nВыберите одну из категорий по ссылке - https://online.metro-cc.ru/ и передайте ссылку мне!")
    print("[-] Пример ссылки: https://online.metro-cc.ru/category/myasnye/myaso/govyadina")
    exit()
else:
    pass


useragents = {"User-Agent" : UserAgent().random}
response = requests.get(SOURCE_URL, headers=useragents)


# Проверяем доступность сайта
async def is_available_url() -> str:
    if response.ok:
        return print(f"[+] Сайт доступен! - Начинаю работу...")
    else:
        print(f"[-] Сайт недоступен! - Код ответа: {response.status_code}")
        exit()


# Получаем информацию о выбраной категории
async def get_category_info() -> str:
    soup = BeautifulSoup(response.text, "lxml")
    category_name = soup.find(class_="subcategory-or-type__heading-title catalog-heading heading__h1").text.strip()
    category_quantity = soup.find(class_="heading-products-count subcategory-or-type__heading-count").text.strip()
    return print(f"[+] Количество товаров в категории {category_name}: {category_quantity}!")


# Получаем имя категории и текущую дату
async def get_any_info():
    return [str(SOURCE_URL[35:].split("/")[-1]), str(datetime.now().date())]


# Получаем ссылки на все страницы категории
async def get_page_quantity() -> list:
    soup = BeautifulSoup(response.text, "lxml")
    all_elements = soup.find(class_="catalog-paginate v-pagination")
    quantity = all_elements.find_all("li")[-2]
    print(f"[+] Кол-во обнаруженых страниц - {quantity.text}!")
    general_url_list = []
    for i in range(1, int(quantity.text)):
        general_url_list.append(SOURCE_URL + f"?page={str(i)}")
    return general_url_list


# Собираем карточки товаров со всех страниц в список
async def get_products_cards():
    all_products_info = []
    all_page_link_list = await get_page_quantity()
    print("[+] Начинаю парсинг карточек товаров...")
    for page in all_page_link_list:
        page_response = requests.get(page, headers=useragents).text
        page_soup = BeautifulSoup(page_response, "lxml")
        all_page_products = page_soup.find_all(class_="catalog-2-level-product-card product-card subcategory-or-type__products-item with-prices-drop")
        for product in all_page_products:
            id = product.get("id")
            name = str(product.find(class_="product-card-name__text").text).strip()
            link = str("https://online.metro-cc.ru" + product.find(class_="product-card-photo__link reset-link").get("href"))
            amount = str(product.find(class_="product-price__sum-rubles").text).strip()
            sale_amount = str(product.find_all(class_="product-price__sum-rubles")[-1].text).strip()
            brand = "brand".replace("\n", "")
            all_products_info.append((id, name, link, amount, sale_amount, brand))
    return all_products_info


async def write_csv():
    any_info = await get_any_info()
    filename = f"{any_info[0]}_{any_info[1]}.csv"
    with open(filename, "w", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(("id", "name", "link", "amount", "sale_amount", "brand"))

    with open(filename, "a", encoding="utf-8") as file:
        writer = csv.writer(file)
        for product in await get_products_cards():
            writer.writerow(product)
        print("[+] Основная масса товаров спаршена! - Осталось немного...")


async def main():
    await is_available_url()
    await get_category_info()
    await write_csv()


if __name__ == "__main__":
    asyncio.run(main())
