import json
import argparse
import requests
from bs4 import BeautifulSoup


HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}


def send_telegram_message(new_items, api_key, chat_id):
    '''
    Send a Telegram message with the new items in the MadridHIFI outlet
    :param new_items: dictionary with the new items
    :param api_key: Telegram API key
    :return: response from Telegram
    '''

    num_new_items = len(new_items)
    title = f'{num_new_items} new products in MadridHIFI outlet!\n'
    requests.get(f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={title}").json()

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
            requests.get(f"https://api.telegram.org/bot{api_key}/sendPhoto?chat_id={chat_id}&photo={image}&caption={message}").json()
        except Exception:
            print("Error sending photo, sending text only")
            requests.get(f"https://api.telegram.org/bot{api_key}/sendMessage?chat_id={chat_id}&text={message}").json()


if __name__ == '__main__':

    # Get api key and chat id as arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("telegram_api_key", help="Telegram API key")
    parser.add_argument("telegram_chat_id", help="Telegram chat ID")
    args = parser.parse_args()

    session = requests.Session()

    # Open last days product JSON
    with open("./products_madridhifi.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    # Send a GET request to the URL
    MAIN_URL = 'https://www.madridhifi.com/outlet/'
    response = session.get(MAIN_URL, headers=HEADERS)

    # Create a BeautifulSoup object
    soup = BeautifulSoup(response.text, "html.parser")
    filters = soup.find_all("a", {"class": "submenu-filter"})
    urls = [
        f"https://www.madridhifi.com{filter['href']}" for filter in filters]

    # Dictionary using name as key. map key to name, price, url and image
    new_products = {}
    for url in urls:
        response = session.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        items_section = soup.find("div", {"class": "list-products"})
        items = items_section.find_all("div", {"class": "product_card"})

        for item in items:
            try:
                name = item.find(
                    "div", {"class": "product_title"}).text.strip()
                price = float(item.find("div", {"class": "actual_price"}).text.strip().split(
                    " ")[0].replace(".", "").replace(",", "."))
                og_price = item.find(
                    "div", {"class": "product_old_price"}).text.strip()
                price_old = float(og_price.split(" ")[0].replace(
                    ".", "").replace(",", ".")) if og_price != "" else price
                url = f"https://www.madridhifi.com{item.find('a')['href']}"
                image = item.find("img")['src']
            except Exception as e:
                print(f'Error parsing item {url}: {e} - Skipping...')
                break

            # Set id form url (https://www.madridhifi.com/p/adam-s2v-reacondicionado/)
            item_id = url.split("/")[-2]

            new_products[item_id] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image
            }

    # new_products["ADAM S2V Monitor de Estudio Activo00 ( REACONDICIONADO )"] = {
    #     "name": "ADAM S2V Monitor de Estudio Activo ( REACONDICIONADO )",
    #     "price": 1566.02,
    #     "price_old": 1999.0,
    #     "url": "https://www.madridhifi.com/p/adam-s2v-reacondicionado/",
    #     "image": "https://www.madridhifi.com/crm/documents/produit/2/6/10118862/photos/listado/s2v-adam.jpg"
    # }
    # new_products["Adam A8H Right Monitor de campo cercano activo00 de 3 v\u00edas Bass Reflex ( REACONDICIONADO )"] = {
    #     "name": "Adam A8H Right Monitor de campo cercano activo de 3 v\u00edas Bass Reflex ( REACONDICIONADO )",
    #     "price": 1331.01,
    #     "price_old": 1799.0,
    #     "url": "https://www.madridhifi.com/p/adam-a8h-right-reacondicionado/",
    #     "image": "https://www.madridhifi.com/crm/documents/produit/1/7/10212671/photos/listado/Adam-A8H-Right-Monitor-de-campo-cercano-activo-de-3-vias-Bass-Reflex.png"
    # }

    # Check if there is a new product by comparing keys
    new_deals = {key: item for key, item in new_products.items()
                 if key not in products_old}

    if new_deals.keys():
        print(f"Found {len(new_deals)} new products! Sending messages...")
        send_telegram_message(new_deals, args.telegram_api_key, args.telegram_chat_id)

    # save as json
    with open("./products_madridhifi.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
