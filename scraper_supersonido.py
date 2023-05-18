import json
import argparse
import requests
from bs4 import BeautifulSoup

API_ENDPOINT = "https://api.mailgun.net/v3/sandbox275ac03099e1436ea6627decb4301641.mailgun.org/messages"
FROM_EMAIL = "Supersonido Outlet <postmaster@sandbox275ac03099e1436ea6627decb4301641.mailgun.org>"
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
    html_body = f'''
    <html>
        <body>
        <h1>{num_new_items} new products in Supersonido outlet!</h1>
    '''
    for key, item in new_items.items():
        url = item['url']
        image = item['image']
        name = item['name']
        price = item['price']
        price_old = item['price_old']
        sale_percentage = round((price_old - price) / price_old * 100, 2)
        html_body += f'''
            <a href="{url}">
                <h3>{name}</h3>
            </a>
            <span style="font-size: 30px;>{price_old}€</span>
            <span style="font-size: 30px; color: blue;">➡️ {price}€</span>
            <span style="font-size: 30px; color: red;">📉 -{sale_percentage}%</span> 
            <br>
            <img src="{image}" height="250">
            <br>
        '''
    html_body += '''
        </body>
    </html>
    '''
    return requests.post(
        API_ENDPOINT,
        auth=("api", api_key),
        data={
            "from": FROM_EMAIL,
            "to": TO_EMAIL,
            "subject": f"🤑 {num_new_items} new products from Supersonido!",
            "text": f"{num_new_items} new items in Supersonido outlet!",
            "html": html_body
        }
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("api_key", help="Mailgun API key")
    args = parser.parse_args()

    session = requests.Session()

    # Open last days product JSON
    with open("./products_supersonido.json", "r", encoding="UTF-8") as file_old:
        products_old = json.load(file_old)

    url = "https://www.supersonido.es/outlet/"  # Replace with the actual URL

    # Send a GET request to the URL using the session object
    response = session.get(url, headers=HEADERS)

    # Create a BeautifulSoup object
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the outlet section
    outlet_section = soup.find("section", {"class": "productos"})

    product_names = outlet_section.find_all("div", {"class": "mt-2"})
    product_prices = outlet_section.find_all("div", {"class": "card-footer"})
    product_urls = outlet_section.find_all("a", {"class": "stretched-link"})
    product_images = outlet_section.find_all("div", {"class": "card-img"})

    # Dictionary using name as the key. Map key to name, price, URL, and image
    new_products = {}
    for name, price_elem, url_elem, image_elem in zip(
        product_names, product_prices, product_urls, product_images
    ):
        name = name.text.strip()
        try:
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

            new_products[name] = {
                "name": name,
                "price": price,
                "price_old": price_old,
                "url": url,
                "image": image,
            }
        except Exception as e:
            print(f"Error with {name}: {e} - Skipping...")
            continue

    # new_products["AudioPro ADDON C5A833"] = {
    #     "name": "AudioPro ADDON C5A",
    #     "price": 199.00,
    #     "price_old": 269.00,
    #     "url": "www.supersonido.es/p/audiopro-addon-c5a__",
    #     "image": "www.supersonido.es/productos/imagenes/producto33149.jpg"
    # }

    # new_products["Supra Cables Regleta Lorad MD06-EU/SP83"] = {
    #         "name": "Supra Cables Regleta Lorad MD06-EU/SP",
    #         "price": 199.00,
    #         "price_old": 230.00,
    #         "url": "www.supersonido.es/p/supra-cables-regleta-lorad-md06-eusp",
    #         "image": "www.supersonido.es/productos/imagenes/producto1476.jpg"
    # }

    print(products_old)

    print('-------')

    # Check if there is a new product by comparing keys
    new_deals = {key: item for key, item in new_products.items()
                 if key not in products_old}

    if new_deals:
        print(f"Found {len(new_deals)} new products! Sending email...")
        # send_simple_message(new_deals, args.api_key)

    print(new_products)

    # Save updated products as JSON
    with open("./products_supersonido.json", "w", encoding='UTF-8') as file_new:
        json.dump(new_products, file_new, indent=4)
