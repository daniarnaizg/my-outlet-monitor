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
    Send a Telegram message with the new items in the Supersonido outlet
    :param new_items: dictionary with the new items
    :param api_key: Telegram API key
    :return: response from Telegram
    '''

    num_new_items = len(new_items)
    title = f'{num_new_items} new products in Supersonido outlet!\n'
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
    with open("./products_supersonido.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    urls = ["https://www.supersonido.es/outlet/", "https://www.supersonido.es/outlet/?Pag=2"]

    # Dictionary using name as the key. Map key to name, price, URL, and image
    new_products = {}
    for page in urls:
        response = session.get(page, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the outlet section
        outlet_section = soup.find("section", {"class": "productos"})

        product_names = outlet_section.find_all("div", {"class": "mt-2"})
        product_prices = outlet_section.find_all("div", {"class": "card-footer"})
        product_urls = outlet_section.find_all("a", {"class": "stretched-link"})
        product_images = outlet_section.find_all("div", {"class": "card-img"})

        for name, price_elem, url_elem, image_elem in zip(
            product_names, product_prices, product_urls, product_images
        ):
            name = name.text.strip()
            try:

                # Skip if not on sale
                if 'PrÃ³ximamente' in price_elem.text:
                    continue # Skip if not on sale
                
                price_parts = price_elem.text.strip().split(" ")
                price = float(price_parts[0].replace(
                    ".", "").replace(",", ".").strip())

                if "\n" in price_parts[1]:
                    price_og = price_parts[1].split("\n")[1].replace(
                        ".", "").replace(",", ".").strip()
                    price_old = float(price_og) if price_og != "" else price
                else:
                    price_old = price

                url = f"www.supersonido.es{url_elem['href']}"
                image = f"www.supersonido.es{image_elem['style'].replace('background-image: url(','').replace(');','')}"

            except Exception as e:
                print(f"Error with {name}: {e} - Skipping...")
                continue


            # Set id form url (www.supersonido.es/p/audiopro-addon-c5a__)
            item_id = url.split("/")[-1]

            new_products[item_id] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image,
            }

    # new_products["AudioPro ADDON C5A833__"] = {
    #     "name": "AudioPro ADDON C5A",
    #     "price": 199.00,
    #     "price_old": 269.00,
    #     "url": "www.supersonido.es/p/audiopro-addon-c5a__",
    #     "image": "www.supersonido.es/productos/imagenes/producto33149.jpg"
    # }

    # new_products["Supra Cables Regleta Lorad MD06-EU/SP83_"] = {
    #         "name": "Supra Cables Regleta Lorad MD06-EU/SP",
    #         "price": 199.00,
    #         "price_old": 230.00,
    #         "url": "www.supersonido.es/p/supra-cables-regleta-lorad-md06-eusp",
    #         "image": "www.supersonido.es/productos/imagenes/producto1476.jpg"
    # }

    # Check if there is a new product by comparing keys
    new_deals = {key: item for key, item in new_products.items()
                 if key not in products_old}

    if new_deals:
        print(f"Found {len(new_deals)} new products! Sending messages...")
        send_telegram_message(new_deals, args.telegram_api_key, args.telegram_chat_id)

    # Save updated products as JSON
    with open("./products_supersonido.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
