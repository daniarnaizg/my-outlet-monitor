import json
import requests
import argparse
from bs4 import BeautifulSoup


def send_simple_message(new_items, api_key):

    # html body that shows the new products in the dicionary new_items. as a table showing images, name and prices
    html_body = f'''
    <html>
        <body>
        <h1>{len(list(new_items.keys()))} new products in MadridHIFI outlet!</h1>

    '''

    for key in new_items.keys():
        url = new_items[key]['url']
        image = new_items[key]['image']
        name = new_items[key]['name']
        price = new_items[key]['price']
        price_old = new_items[key]['price_old']
        sale_percentage = round((price_old - price) / price * 100, 2)

        html_body += f'''
                <a href="{url}">
                    <h3>{name}</h3>
                </a>
                <span>{price_old} €</span>
                <span> → </span>
                <span style="font-size: 20px; color: blue;">{price} €</span>
                <span style="font-size: 30px; color: red;">{sale_percentage}%</span> 
                <br>
                <img src="{image}" height="250">
                <br>
        '''

    html_body += '''

        </body>
    </html>
    '''

    return requests.post(
        "https://api.mailgun.net/v3/sandbox275ac03099e1436ea6627decb4301641.mailgun.org/messages",
        auth=("api", api_key),
        data={"from": "MadridHIFI Outlet <postmaster@sandbox275ac03099e1436ea6627decb4301641.mailgun.org>",
              "to": "Dani Arnaiz <daniarnaizg@gmail.com>",
              "subject": f"{len(list(new_items.keys()))} new products from MadridHIFI!",
              "text": f"{len(list(new_items.keys()))} new items in MadridHIFI outlet!",
              "html": html_body})


if __name__ == '__main__':

    # get api key as argument
    parser = argparse.ArgumentParser()
    parser.add_argument("api_key", help="Mailgun API key")
    args = parser.parse_args()

    HEADERS = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

    # Open last days product JSON
    with open("./products_madridhifi.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    # Send a GET request to the URL
    main_url = 'https://www.madridhifi.com/outlet/'
    response = requests.get(main_url, headers=HEADERS)

    # Create a BeautifulSoup object
    soup = BeautifulSoup(response.text, "html.parser")
    filters = soup.find_all("a", {"class": "submenu-filter"})
    urls = [
        f"https://www.madridhifi.com{filter['href']}" for filter in filters]

    urls = urls

    # dictionary using name as key. map key to name, price, url and image
    new_products = {}

    for url in urls:
        # print(url)
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        items_section = soup.find("div", {"class": "list-products"})
        items = items_section.find_all("div", {"class": "product_card"})
        for item in items:

            try:
                name = item.find(
                    "div", {"class": "product_title"}).text.strip()
                price = float(item.find("div", {"class": "actual_price"}).text.strip().split(
                    " ")[0].replace(".", "").replace(",", "."))
                og_price = item.find("div", {"class": "product_old_price"}).text.strip()
                price_old = float(og_price.split(" ")[0].replace(".", "").replace(",", ".")) if og_price != "" else price
                url = f"https://www.madridhifi.com{item.find('a')['href']}"
                image = item.find("img")['src']
            except:
                print(f'Error parsing item {url}, skipping...')
                continue

            new_products[name] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image
            }
    
    # new item test
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

    # check if there is a new product by checking keys
    # if there is a new product, send a message to the user
    new_deals = {}
    for key in list(new_products.keys()):
        if key not in list(products_old.keys()):
            new_deals[key] = new_products[key]
            print(f"New product: {key}")

    if new_deals.keys():
        send_simple_message(new_deals, args.api_key)

    # save as json
    with open("./products_madridhifi.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)

