import json
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

# Open last days product JSON
with open("./products.json", "r", encoding="UTF-8") as file_old:
    products_old = json.load(file_old)

# Send a GET request to the URL
url = "https://www.supersonido.es/outlet/"  # Replace with the actual URL
response = requests.get(url, headers=HEADERS)

# Create a BeautifulSoup object
soup = BeautifulSoup(response.text, "html.parser")

# Find the outlet section
outlet_section = soup.find("section", {"class": "productos"})

product_names = outlet_section.find_all("div", {"class": "mt-2"})
product_prices = outlet_section.find_all("div", {"class": "card-footer"})
product_urls = outlet_section.find_all("a", {"class": "stretched-link"})
product_images = outlet_section.find_all("div", {"class": "card-img"})

# print(product_names[1].text.strip())
# print(product_prices[1].text.strip().split(" ")[0])
# print(product_prices[1].text.strip().split(" ")[1].split("â\x82¬")[1].replace("\n","").strip())
# print(f"www.supersonido.es{product_urls[1]['href']}")
# print(f"www.supersonido.es{product_images[1]['style'].replace('background-image: url(','').replace(');','')}")

# dictionary using name as key. map key to name, price, url and image
new_products = {}
for i in range(len(product_names)):
    name = product_names[i].text.strip()
    new_products[name] = {
        "name": name,
        "price": product_prices[i].text.strip().split(" ")[0],
        "price_new": product_prices[i].text.strip().split(" ")[1].split("â\x82¬")[1].replace("\n","").strip() if "â\x82¬" in product_prices[i].text.strip() else "",
        "url": f"www.supersonido.es{product_urls[i]['href']}",
        "image": f"www.supersonido.es{product_images[i]['style'].replace('background-image: url(','').replace(');','')}"
    }


# new item test
new_products["new_item"] = {
        "name": "new_item",
        "price": "12",
        "price_new": "14",
        "url": f"www.supersonido.es",
        "image": f"www.supersonido.es"
    }

# check if there is a new product by checking keys
# if there is a new product, send a message to the user
for key in list(new_products.keys()):
    if key not in list(products_old.keys()):
        print(f"New product: {key}")

# print(new_products[list(new_products.keys())[0]])
# print(new_products[list(new_products.keys())[1]])
# print(new_products[list(new_products.keys())[2]])
# print('â\x82¬\n339,00'.strip())

# save as json
with open("./products.json", "w", encoding='UTF-8') as file_new:
    json.dump(new_products, file_new, indent=4)
