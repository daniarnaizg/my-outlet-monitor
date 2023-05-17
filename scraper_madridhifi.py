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
        price = float(new_items[key]['price'].replace(
            ".", "").replace(",", "."))
        price_new = float(new_items[key]['price_new'].replace(
            ".", "").replace(",", "."))
        sale_percentage = round((price - price_new) / price * 100, 2)

        html_body += f'''
                <a href="{url}">
                    <h3>{name}</h3>
                </a>
                <span>{price_new} €</span>
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
        data={"from": "Supersonido Outlet <postmaster@sandbox275ac03099e1436ea6627decb4301641.mailgun.org>",
              "to": "Dani Arnaiz <daniarnaizg@gmail.com>",
              "subject": f"{len(list(new_items.keys()))} new products from MadridHIFI!",
              "text": f"{len(list(new_items.keys()))} new items in MadridHIFI outlet!",
              "html": html_body})


if __name__ == '__main__':

    # get api key as argument
    # parser = argparse.ArgumentParser()
    # parser.add_argument("api_key", help="Mailgun API key")
    # args = parser.parse_args()

    HEADERS = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    }

    # Open last days product JSON
    # with open("./products_madridhifi.json", "r", encoding="UTF-8") as file_old:
    #     products_old = json.load(file_old)

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
                og_price = float(item.find("div", {"class": "product_old_price"}).text.strip())
                price_new = float(og_price.split(" ")[0].replace(".", "").replace(",", ".")) if og_price is not "" else price
                url = f"https://www.madridhifi.com{item.find('a')['href']}"
                image = item.find("img")['src']
            except:
                print("Error", name, url)
                continue

            new_products[name] = {
                "name": name,
                "price": price,
                "price_new": price_new,
                "url": url,
                "image": image
            }
    
    # new item test
    # new_products["AudioPro ADDON C5A833"] = {
    #     "name": "AudioPro ADDON C5A",
    #     "price": "199,00",
    #     "price_new": "269,00",
    #     "url": "www.supersonido.es/p/audiopro-addon-c5a__",
    #     "image": "www.supersonido.es/productos/imagenes/producto33149.jpg"
    # }

    # new_products["Supra Cables Regleta Lorad MD06-EU/SP83"] = {
    #         "name": "Supra Cables Regleta Lorad MD06-EU/SP",
    #         "price": "199,00",
    #         "price_new": "230,00",
    #         "url": "www.supersonido.es/p/supra-cables-regleta-lorad-md06-eusp",
    #         "image": "www.supersonido.es/productos/imagenes/producto1476.jpg"
    # }

    # check if there is a new product by checking keys
    # if there is a new product, send a message to the user
    # new_deals = {}
    # for key in list(new_products.keys()):
    #     if key not in list(products_old.keys()):
    #         new_deals[key] = new_products[key]
    #         print(f"New product: {key}")

    # if new_deals.keys():
    #     send_simple_message(new_deals, args.api_key)


    # save as json
    with open("./products_madridhifi.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)

