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
        sale_percentage = round((price_old - price) / price_old * 100, 2)
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

    session = requests.Session()

    # Open last days product JSON
    with open("./products_mag.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    urls = ["https://www.mag-outlet.com/49-super-ofertas?id_category=49&n=55"]

    # Dictionary using name as the key. Map key to name, price, URL, and image
    new_products = {}
    for page in urls:
        response = session.get(page, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the outlet section
        outlet_section = soup.find("ul", {"id": "product_list"})

        items = outlet_section.find_all("div", {"class": "product-container"})

        for item in items:
            try:

                name = item.find("a", {"class": "product-name"}).text.strip()
                url = item.find("a", {"class": "product_img_link"})["href"]
                image = item.find("img", {"class": "replace-2x"})["src"]
                price = float(item.find("span", {"class": "price product-price"}).text.strip(
                ).replace("€", "").replace(",", ".").replace(" ", ""))

                try:
                    price_old = float(item.find("span", {"class": "old-price product-price"}).text.strip(
                    ).replace("€", "").replace(",", ".").replace(" ", ""))
                except:
                    # No price_old, using price
                    price_old = price

            except Exception as e:
                print(f'Error with {url}: {e} - Skipping...')
                continue

            # set id form url (https://www.mag-outlet.com/inicio/700-jamo-c-95-dark-apple.html)
            item_id = url.split("/")[-1].split(".")[0]

            new_products[item_id] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image,
            }

    # new_products["700-jamo-c-95-dark-apple222"] = {
    #     "name": "Jamo C 95 Dark Apple",
    #     "price": 179.55,
    #     "price_old": 399.0,
    #     "url": "https://www.mag-outlet.com/inicio/700-jamo-c-95-dark-apple.html",
    #     "image": "https://www.mag-outlet.com/1175-home_default/jamo-c-95-dark-apple.jpg"
    # }

    # new_products["426-klipsch-rp-160m-ebony"] = {
    #     "name": "Klipsch RP-160M Ebony",
    #     "price": 399.0,
    #     "price_old": 649.0,
    #     "url": "https://www.mag-outlet.com/in-the-home/426-klipsch-rp-160m-ebony.html",
    #     "image": "https://www.mag-outlet.com/704-home_default/klipsch-rp-160m-ebony.jpg"
    # }

    # Check if there is a new product by comparing keys
    new_deals = {key: item for key, item in new_products.items()
                 if key not in products_old}

    if new_deals:
        print(f"Found {len(new_deals)} new products! Sending messages...")
        send_telegram_message(new_deals, args.telegram_api_key, args.telegram_chat_id)

    # Save updated products as JSON
    with open("./products_mag.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
