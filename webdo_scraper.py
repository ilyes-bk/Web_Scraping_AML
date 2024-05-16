import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
import dateparser
import logging
from googletrans import Translator

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


def translate_frensh_to_english(text):
    translator = Translator()
    translated_text = translator.translate(text, src='fr', dest='en').text
    return translated_text


def get_webdo_pages(nbr_pages):
    logging.info("Generating pages links")
    pages_links = []
    for i in range(1, nbr_pages + 1):
        url = "https://www.webdo.tn/fr/search?q=politique&page=" + str(i)
        logging.info(f"generating : {url}")
        pages_links.append(url)
    return pages_links


def get_webdo_articles_links(pages_links):
    articles_links = []
    try:
        for link in pages_links:
            logging.info(f"Get the ads links from : {link}")
            # Create a session to handle cookies
            session = requests.Session()
            # Add headers to the session
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/100.0.0.0"
            }
            session.headers.update(headers)
            # Send a GET request to the website
            response = session.get(link)
            soup = BeautifulSoup(response.content, 'lxml')
            page = soup.find("div", class_="posts-listing")
            ad_div = page.find_all("div", class_="col-xs-12 col-sm-6 col-md-3")
            for ad in ad_div:
                link_div = ad.find("h3", class_="post__title typescale-0")
                article_link = link_div.a.get("href")
                logging.info(article_link)
                articles_links.append(article_link)
    except:
        pass
    return articles_links


def scrape_webdo(links):
    articles = []
    for link in links:
        try:
            logging.info(f"Get article data from : {link}")
            # Create a session to handle cookies
            session = requests.Session()

            # Add headers to the session
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 OPR/100.0.0.0"
            }
            session.headers.update(headers)
            # Send a GET request to the website
            response = session.get(link)
            session.close()
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml")
                article = {"art_url": link}
                title = soup.find("h1", class_="entry-title")
                article_title = (" ".join(title.get_text().split())).lower().strip()
                article['art_title'] = article_title
                try:
                    publish_date = soup.find("time", class_="entry-date published")
                    publish_date = publish_date.get_text().strip()
                    article["art_published_at"] = dateparser.parse(publish_date, date_formats=["%Y-%m-%d %H:%M:%S.%f"])
                except:
                    article["art_published_at"] = None

                try:
                    article_type = soup.find("a", class_="entry-cat cat-theme cat-5")
                    article["art_type"] = article_type.get_text().strip()
                except:
                    article["art_type"] = None
                article_content = soup.find("div",
                                            class_="single-body entry-content typography-copy").get_text().strip()
                # Remove extra spaces and line breaks
                article_content = re.sub(r'\s+', ' ', article_content).strip()
                article["art_content"] = translate_frensh_to_english(article_content)
                # Fixed Features
                article["art_category"] = "politics"
                article["inactive"] = False
                article["country_code"] = "TN"
                # article : resulted_from scraping
                article['scrapped_by'] = BOT_NAME
                article['art_source'] = BASE_SRC
                article["art_creation_date"] = datetime.utcnow()
                articles.append(article)
            response.close()
        except:
            pass
    return articles


if __name__ == '__main__':
    BASE_SRC = 'https://www.webdo.tn/fr'
    BOT_NAME = 'webdo_tn.bot'
    webdo_pages_links = get_webdo_pages(3)#24
    webdo_ads_links = get_webdo_articles_links(webdo_pages_links)
    articles_dataset = scrape_webdo(webdo_ads_links)
    logging.info(f"Number of articles : {len(webdo_ads_links)}")
    logging.info(webdo_ads_links)
    logging.info(f"articles scraping RESULTS :  {articles_dataset}")

    file_name = "webdo_articles.json"

    # Serialize the data to a JSON-formatted string
    json_data = json.dumps(articles_dataset, default=str)

    # Write the JSON data to the file
    with open(file_name, "w", encoding="UTF-8") as json_file:
        json_file.write(json_data)

    logging.info(f"JSON data has been saved to {file_name}")
