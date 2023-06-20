import json
import argparse
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import math

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}


def send_telegram_message(new_items, api_key, chat_id):
    '''
    Send a Telegram message with the new items in the MAG Outlet outlet
    :param new_items: dictionary with the new items
    :param api_key: Telegram API key
    :return: response from Telegram
    '''

    num_new_items = len(new_items)
    title = f'{num_new_items} new products in MAG Outlet outlet!\n'
    requests.get(
        f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={title}").json()

    for key, item in new_items.items():
        url = item['url']
        image = item['image']
        name = item['name']
        price = item['price']
        price_old = item['price_old']
        try:
            sale_percentage = round((price_old - price) / price_old * 100, 2)
        except ZeroDivisionError:
            sale_percentage = 0
        message = f'''
        {name}
        {price_old}€ ➡️ {price}€ 📉 -{sale_percentage}% 
        {url}
        '''

        try:
            requests.get(
                f"https://api.telegram.org/bot{api_key}/sendPhoto?chat_id={chat_id}&photo={image}&caption={message}").json()
        except Exception:
            print("Error sending photo, sending text only")
            requests.get(
                f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={message}").json()


if __name__ == '__main__':

    # Get api key and chat id as arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("telegram_api_key", help="Telegram API key")
    parser.add_argument("telegram_chat_id", help="Telegram chat ID")
    args = parser.parse_args()

    # Open last days product JSON
    with open("./products_zococity.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    # HTMLSession
    url = "https://zococity.es/collections/outlet"
    session = HTMLSession()
    response = session.get(url, headers=HEADERS)
    response.html.render()

    # Get the HTML content
    soup = BeautifulSoup(response.html.html, "html.parser")

    # get number of products from the top (<span class="gf-summary"><b>158</b> Productos</span>)
    num_products = int(soup.find("span", {"class": "gf-summary"}).text.split()[0])

    # get the number of pages
    num_pages = math.ceil(num_products / 30)
    urls = [f"https://zococity.es/collections/outlet?page={i}" for i in range(1, num_pages + 1)]

    # Dictionary using name as the key. Map key to name, price, URL, and image
    new_products = {}
    for page in urls:

        session = HTMLSession()
        response = session.get(page, headers=HEADERS)
        response.html.render()
        soup = BeautifulSoup(response.html.html, "html.parser")

        # Find the outlet section
        outlet_section = soup.find("div", {"id": "gf-products"})

        items = outlet_section.find_all("div", {"class": "product-card col"})

        for item in items:
            try:
                name = item.find("div", {"class": "product-card__ttl"}).text.strip()
                url = item.find("div", {"class": "product-card__ttl"}).find("a")["href"]
                url = f"https://zococity.es{url}"
                image = item.find("img", {"class": "product-card__img"})["data-src"].split("?")[0]
                price = item.find("span", {"class": "price-item"}).text.strip().replace("€", "").replace(".", "").replace(",", ".")
                if 'from' in price.lower():
                    price = float(price.split(" ")[-1])
                else:
                    price = float(price)

                try:
                    price_old = float(item.find("s", {"class": "price-item"}).text.strip().replace("€", "").replace(".", "").replace(",", "."))
                except:
                    # No price_old, using price
                    price_old = price

            except Exception as e:
                print(f'Error with {url}: {e}')
                continue

            
            # set id form url (https://zococity.es/products/edifier-r33bt-reacondicionado)
            item_id = url.split("/")[-1]

            new_products[item_id] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image,
            }

    # new_products["700-jamo-c-95-dark-apple2223"] = {
    #     "name": "Soundmagic HP1000 - Reacondicionados",
    #     "price": 263.2,
    #     "price_old": 329.0,
    #     "url": "https://zococity.es/products/soundmagic-hp1000-reacondicionados",
    #     "image": "https://cdn.shopify.com/s/files/1/0528/8008/1052/products/hp1000_1_9bf3d72d-ad02-47fc-b102-da27c147c775_360x.jpg"
    # }

    # new_products["fiio-l27-reacondicionado223"] = {
    #     "name": "FiiO L27 - Reacondicionado",
    #     "price": 15.99,
    #     "price_old": 19.99,
    #     "url": "https://zococity.es/products/fiio-l27-reacondicionado",
    #     "image": "https://cdn.shopify.com/s/files/1/0528/8008/1052/products/screenshot_2_2_360x.jpg"
    # }

    # Check if there is a new product by comparing keys
    new_deals = {key: item for key, item in new_products.items()
                 if key not in products_old}

    if new_deals:
        print(f"Found {len(new_deals)} new products! Sending messages...")
        send_telegram_message(new_deals, args.telegram_api_key, args.telegram_chat_id)

    # Save updated products as JSON
    with open("./products_zococity.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
