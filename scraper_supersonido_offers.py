from supersonido_utils import OffersScraper, HEADERS, BASE_URL

if __name__ == '__main__':
    parser = OffersScraper.get_common_parser("Supersonido Offers Scraper")
    parser.add_argument("--pages", type=int, default=5, help="Number of pages to scrape")
    parser.add_argument("--discount", type=int, default=40, 
                      help="Minimum discount percentage to notify")
    args = parser.parse_args()
    
    # Set custom filename
    args.json_filename = "offers_supersonido.json"
    
    scraper = OffersScraper(BASE_URL, HEADERS, pages=args.pages)
    scraper.discount_threshold = args.discount
    scraper.run(args)
