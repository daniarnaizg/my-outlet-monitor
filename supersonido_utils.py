import json
import argparse
import time
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
} 

BASE_URL = "https://www.supersonido.es"

class BaseScraper:
    """Base class for Supersonido scrapers with common functionality"""
    URL_PATH = ""  # To be defined in subclasses
    
    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url = base_url
        self.headers = headers
        self.session = requests.Session()

    @staticmethod
    def parse_prices(price_text: str) -> tuple[float, float]:
        """Extract current and old prices from price text"""
        price_parts = price_text.strip().split(" ")
        current_price = float(price_parts[0].replace(".", "").replace(",", "."))
        
        old_price = current_price
        if len(price_parts) > 1 and "\n" in price_parts[1]:
            old_price_str = price_parts[1].split("\n")[1].replace(".", "").replace(",", ".").strip()
            if old_price_str:
                old_price = float(old_price_str)
        
        return current_price, old_price

    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with error handling"""
        try:
            response = self.session.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def extract_product_data(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """Extract product data from parsed HTML"""
        products = {}
        outlet_section = soup.find("section", class_="productos")
        
        if not outlet_section:
            return products

        items = zip(
            outlet_section.find_all("div", class_="mt-2"),
            outlet_section.find_all("div", class_="card-footer"),
            outlet_section.find_all("a", class_="stretched-link"),
            outlet_section.find_all("div", class_="card-img")
        )

        for name_elem, price_elem, url_elem, image_elem in items:
            product = self._extract_single_product(name_elem, price_elem, url_elem, image_elem)
            if product:
                products[product['id']] = product

        return products

    def _extract_single_product(self, name_elem, price_elem, url_elem, image_elem) -> Optional[Dict]:
        """Extract data for a single product"""
        try:
            if 'Próximamente' in price_elem.text:
                return None

            name = name_elem.text.strip()
            current_price, old_price = self.parse_prices(price_elem.text)
            product_url = f"{self.base_url}{url_elem['href']}"
            image_url = self._extract_image_url(image_elem)
            
            # Calculate sale percentage
            sale_pct = 0
            if old_price > current_price:
                sale_pct = round(((old_price - current_price) / old_price) * 100, 1)

            return {
                "id": product_url.split("/")[-1],
                "name": name,
                "price": current_price,
                "price_old": old_price,
                "sale_percentage": sale_pct,
                "url": product_url,
                "image": image_url
            }
        except Exception as e:
            print(f"Error processing product: {e}")
            return None

    def _extract_image_url(self, image_elem) -> str:
        """Extract clean image URL from style attribute"""
        style = image_elem.get('style', '')
        return f"{self.base_url}{style.split('url(')[-1].split(')')[0]}" if style else ''

    @staticmethod
    def load_previous_data(filename: str) -> Dict:
        """Load previously saved data from JSON file"""
        try:
            with open(filename, "r", encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_data(self, data: Dict, filename: str) -> None:
        """Save data to JSON file"""
        try:
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved {len(data)} items to {filename}")
        except Exception as e:
            print(f"Error saving data: {e}")

    @staticmethod
    def get_common_parser(description: str) -> argparse.ArgumentParser:
        """Create common argument parser for all scrapers"""
        parser = argparse.ArgumentParser(description=description)
        parser.add_argument("telegram_api_key", help="Telegram API key")
        parser.add_argument("telegram_chat_id", help="Telegram chat ID")
        parser.add_argument("--json_filename", default="data.json", 
                          help="JSON filename for storing results")
        parser.add_argument("--message_title", default="New items found!",
                          help="Title for Telegram notifications")
        return parser

    def generate_urls(self, pages: int) -> List[str]:
        """Generate page URLs for the specific section"""
        return [
            f"{self.base_url}/{self.URL_PATH}/?Pag={i}"
            for i in range(1, pages + 1)
        ]

    def _send_product_notifications(self, items: Dict, api_key: str, chat_id: str, 
                                  header_template: str, product_template: str) -> None:
        """Generic notification sender with templated messages"""
        self._send_telegram_message(api_key, chat_id, header_template)
        
        for product in items.values():
            message = product_template.format(
                name=product['name'],
                price=product['price'],
                price_old=product['price_old'],
                sale_pct=product['sale_percentage'],
                url=product['url']
            )
            
            if product['image']:
                self._send_telegram_photo(api_key, chat_id, product['image'], message)
            else:
                self._send_telegram_message(api_key, chat_id, message)
            
            time.sleep(1)


class OutletScraper(BaseScraper):
    """Scraper for regular outlet products"""
    URL_PATH = "outlet"
    HEADER_TEMPLATE = "🛍️ {count} nuevos en outlet"
    PRODUCT_TEMPLATE = (
        "🔥 {name}\n"
        "💶 {price_old}€ ➡️ {price}€ 📉-{sale_pct}%\n"
        "🔗 {url}"
    )
    
    def __init__(self, base_url: str, headers: Dict[str, str], pages: int = 2):
        super().__init__(base_url, headers)
        self.pages = pages

    def run(self, args) -> None:
        """Main execution flow for outlet scraper"""
        urls = self.generate_urls(self.pages)
        current_products = self._fetch_all_products(urls)
        new_products = self._find_new_products(current_products, args.json_filename)

        if new_products:
            self._handle_notifications(new_products, args)
        
        self.save_data(current_products, args.json_filename)
        print(f"Saved {len(current_products)} products")

    def _fetch_all_products(self, urls: List[str]) -> Dict:
        """Fetch products from all URLs"""
        products = {}
        for url in urls:
            if soup := self.fetch_page(url):
                products.update(self.extract_product_data(soup))
        return products

    def _find_new_products(self, current: Dict, filename: str) -> Dict:
        """Identify new products since last run"""
        previous = self.load_previous_data(filename)
        return {k: v for k, v in current.items() if k not in previous}

    def _handle_notifications(self, new_products: Dict, args) -> None:
        """Handle Telegram notifications"""
        print(f"Found {len(new_products)} new OUTLET products! Notifying...")
        self.send_telegram_notification(
            new_products,
            args.telegram_api_key,
            args.telegram_chat_id,
            args.message_title
        )

    def send_telegram_notification(self, items: Dict, api_key: str, 
                                 chat_id: str, title: str) -> None:
        self._send_product_notifications(
            items,
            api_key,
            chat_id,
            self.HEADER_TEMPLATE.format(count=len(items)),
            self.PRODUCT_TEMPLATE
        )

    @staticmethod
    def _send_telegram_message(api_key: str, chat_id: str, text: str) -> None:
        """Low-level Telegram message sending with error handling"""
        try:
            url = f"https://api.telegram.org/bot{api_key}/sendMessage"
            params = {'chat_id': chat_id, 'text': text}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send Telegram message: {e}")

    @staticmethod
    def _send_telegram_photo(api_key: str, chat_id: str, photo_url: str, caption: str = "") -> None:
        """Send photo through Telegram API"""
        try:
            url = f"https://api.telegram.org/bot{api_key}/sendPhoto"
            params = {
                'chat_id': chat_id,
                'photo': photo_url,
                'caption': caption[:1000]  # Truncate to Telegram's limit
            }
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to send Telegram photo: {e}")
            # Fallback to text message
            OutletScraper._send_telegram_message(api_key, chat_id, caption)


class OffersScraper(OutletScraper):
    """Scraper for special offers with discount filtering"""
    URL_PATH = "ofertas"
    HEADER_TEMPLATE = "🎉 {count} ofertas >{threshold}%"
    PRODUCT_TEMPLATE = (
        "🚨 {name}\n"
        "💶 {price_old}€ ➡️ {price}€ 📉-{sale_pct}%\n"
        "🔗 {url}"
    )
    
    def __init__(self, base_url: str, headers: Dict[str, str], pages: int = 2):
        super().__init__(base_url, headers, pages)
        self.discount_threshold = 40

    def run(self, args) -> None:
        """Main execution flow for offers scraper"""
        urls = self.generate_urls(self.pages)
        current_products = self._fetch_all_products(urls)
        
        # First filter by discount threshold
        filtered_products = {
            pid: product for pid, product in current_products.items()
            if self._is_significant_discount(product)
        }
        
        # Then find new products from filtered list
        new_products = self._find_new_products(filtered_products, args.json_filename)
        
        if new_products:
            self._handle_notifications(new_products, args)
        
        # Save only filtered products that meet criteria
        self.save_data(filtered_products, args.json_filename)
        print(f"Saved {len(filtered_products)} qualified offers")

    def _find_new_products(self, current: Dict, filename: str) -> Dict:
        """Identify new products from filtered list"""
        previous = self.load_previous_data(filename)
        return {pid: product for pid, product in current.items() if pid not in previous}

    def _is_significant_discount(self, product: Dict) -> bool:
        """Check if product meets discount threshold"""
        try:
            old_price = product['price_old']
            current_price = product['price']
            if old_price <= current_price:
                return False
            return ((old_price - current_price) / old_price * 100) > self.discount_threshold
        except KeyError:
            return False

    def _handle_notifications(self, new_products: Dict, args) -> None:
        """Handle Telegram notifications"""
        print(f"Found {len(new_products)} new OFFERS (>{self.discount_threshold}% discount)! Notifying...")
        self.send_telegram_notification(
            new_products,
            args.telegram_api_key,
            args.telegram_chat_id,
            args.message_title
        )

    def send_telegram_notification(self, items: Dict, api_key: str, 
                                 chat_id: str, title: str) -> None:
        header = self.HEADER_TEMPLATE.format(
            count=len(items),
            threshold=self.discount_threshold
        )
        self._send_product_notifications(
            items,
            api_key,
            chat_id,
            header,
            self.PRODUCT_TEMPLATE
        )
