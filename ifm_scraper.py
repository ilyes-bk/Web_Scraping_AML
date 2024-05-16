import requests
from bs4 import BeautifulSoup
import re
import dateparser
from datetime import datetime
import json
import logging
from googletrans import Translator

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


def translate_arabic_to_english(text):
    translator = Translator()
    translated_text = translator.translate(text, src='ar', dest='en').text
    return translated_text


def get_ifm_pages(nbr_pages):
    logging.info("Generating pages links")
    pages_links = []
    for i in range(1, nbr_pages + 1):
        url = "https://www.ifm.tn/ar/articles/سياسة/2?page=" + str(i)
        logging.info(f"generating : {url}")
        pages_links.append(url)
    return pages_links


def get_ifm_articles_links(pages_links):
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
            page = soup.find('div', class_="col-md-8 col-sm-7 dual-posts padding-bottom-30")
            ad_div = page.find_all("div", class_="row")
            for ad in ad_div:
                link_div = ad.find("h4")
                article_link = link_div.a.get("href")
                articles_links.append(article_link)
    except:
        pass
    return articles_links


def scrape_ifm(links):
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
                title = soup.find("div", class_="blog-single-head margin-top-25")
                article_title = (" ".join(title.h2.get_text().split())).lower().strip()
                article['art_title'] = article_title
                try:
                    publish_date = soup.find("span", class_="date")
                    publish_date = publish_date.get_text().strip()
                    # Replace "À" with a space
                    publish_date = dateparser.parse(publish_date)
                    # Define the format of the date and time string
                    art_published_at = publish_date.strftime("%Y-%m-%d %H:%M:%S.%f")
                    # Define the format of the input string
                    date_format = '%Y-%m-%d %H:%M:%S.%f'

                    # Parse the string and create a datetime object
                    article["art_published_at"] = datetime.strptime(art_published_at, date_format)
                except:
                    article["art_published_at"] = None

                article_content = soup.find("div", class_="intro").get_text().strip()
                article_content_1 = soup.find("div", class_="coprs").get_text().strip()
                # Remove extra spaces and line breaks
                article_content = article_content + article_content_1
                article_content = re.sub(r'\s+', ' ', article_content).strip()
                article["art_content"] = translate_arabic_to_english(article_content)
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
    BASE_SRC = 'https://www.ifm.tn/ar'
    BOT_NAME = 'ifm-ar.bot'
    ifm_pages_links = get_ifm_pages(3) #930
    ifm_ads_links = get_ifm_articles_links(ifm_pages_links)
    articles_dataset = scrape_ifm(ifm_ads_links)
    logging.info(f"Number of articles : {len(ifm_ads_links)}")
    logging.info(ifm_ads_links)
    logging.info(f"articles scraping RESULTS :  {articles_dataset}")
    logging.info(f"NUMBER OF ARTICLES {len(articles_dataset)}")
    file_name = "ifm_articles.json"

    # Serialize the data to a JSON-formatted string
    json_data = json.dumps(articles_dataset, ensure_ascii=False, default=str)

    # Write the JSON data to the file
    with open(file_name, "w", encoding="utf-8") as json_file:
         json_file.write(json_data)

    logging.info(f"JSON data has been saved to {file_name}")