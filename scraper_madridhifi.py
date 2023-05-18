import json
import argparse
import requests
from bs4 import BeautifulSoup

API_ENDPOINT = "https://api.mailgun.net/v3/sandbox275ac03099e1436ea6627decb4301641.mailgun.org/messages"
FROM_EMAIL = "MadridHIFI Outlet <postmaster@sandbox275ac03099e1436ea6627decb4301641.mailgun.org>"
TO_EMAIL = "Dani Arnaiz <daniarnaizg@gmail.com>"

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}


def send_simple_message(new_items, api_key):
    '''
    Send an email with the new items in the Supersonido outlet
    :param new_items: dictionary with the new items
    :param api_key: Mailgun API key
    :return: response from Mailgun
    '''

    num_new_items = len(new_items)
    html_body = f"<html><body><h1>{num_new_items} new products in MadridHIFI outlet!</h1>"

    for key, item in new_items.items():
        email_url = item['url']
        email_image = item['image']
        email_name = item['name']
        email_price = item['price']
        email_price_old = item['price_old']
        sale_percentage = round((price_old - price) / price_old * 100, 2)
        html_body += f'''
            <a href="{email_url}">
                <h3>{email_name}</h3>
            </a>
            <span style="font-size: 30px;>{email_price_old}€</span>
            <span style="font-size: 30px; color: blue;">➡️ {email_price}€</span>
            <span style="font-size: 30px; color: red;">📉 -{sale_percentage}%</span> 
            <br>
            <img src="{email_image}" height="250">
            <br>
        '''

    html_body += "</body></html>"

    return requests.post(
        API_ENDPOINT,
        auth=("api", api_key),
        data={
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": f"🤑 {num_new_items} new products from MadridHIFI!",
            "text": f"{num_new_items} new items in MadridHIFI outlet!",
            "html": html_body
        }
    )


if __name__ == '__main__':

    # get api key as argument
    parser = argparse.ArgumentParser()
    parser.add_argument("api_key", help="Mailgun API key")
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

    # dictionary using name as key. map key to name, price, url and image
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

            new_products[name] = {
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
        print(f"Found {len(new_deals)} new products! Sending email...")
        send_simple_message(new_deals, args.api_key)

    # save as json
    with open("./products_madridhifi.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
