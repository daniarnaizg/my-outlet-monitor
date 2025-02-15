from supersonido_utils import OutletScraper, HEADERS, BASE_URL

if __name__ == '__main__':
    parser = OutletScraper.get_common_parser("Supersonido Outlet Scraper")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages to scrape")
    args = parser.parse_args()

    scraper = OutletScraper(BASE_URL, HEADERS, pages=args.pages)
    scraper.run(args)
