import requests
from bs4 import BeautifulSoup
import re
import dateparser
from datetime import datetime
import json
import logging
from googletrans import Translator

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', level=logging.INFO)


def translate_frensh_to_english(text):
    translator = Translator()
    translated_text = translator.translate(text, src='fr', dest='en').text
    return translated_text


def get_kapitalis_pages(nbr_pages):
    logging.info("Generating pages links")
    pages_links = []
    for i in range(1, nbr_pages + 1):
        url = "https://kapitalis.com/tunisie/category/politique/page/" + str(i) + "/"
        logging.info(f"generating : {url}")
        pages_links.append(url)
    return pages_links


def get_kapitalis_articles_links(pages_links):
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
            page = soup.find('div', class_="cmsmasters_archive")
            ad_div = page.find_all("article")
            for ad in ad_div:
                link_div = ad.find("figure", class_="cmsmasters_img_wrap")
                article_link = link_div.a.get("href")
                articles_links.append(article_link)
    except:
        pass
    return articles_links


def scrape_kapitalis(links):
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
                title = soup.find("header", class_="cmsmasters_post_header entry-header")
                article_title = (" ".join(title.get_text().split())).lower().strip()
                article['art_title'] = article_title
                try:
                    publish_date = soup.find("abbr", class_="published")
                    publish_date = publish_date.get_text().strip()
                    article["art_published_at"] = dateparser.parse(publish_date, date_formats=["%Y-%m-%d %H:%M:%S.%f"])
                except:
                    article["art_published_at"] = None

                article_content = soup.find("div", class_="cmsmasters_post_content entry-content")
                # Find all <p> tags within the <div>
                p_tags = article_content.find_all('p')
                p_tags.pop()
                # Extract the text from each <p> tag, concatenate, and remove extra spaces
                concatenated_text = ' '.join([p.get_text(strip=True) for p in p_tags])
                # Remove extra spaces and line breaks
                concatenated_text = re.sub(r'\s+', ' ', concatenated_text).strip()
                article["art_content"] = translate_frensh_to_english(concatenated_text)
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
    BASE_SRC = 'https://kapitalis.com/tunisie/'
    BOT_NAME = 'kapitalis.bot'
    kapitalis_pages_links = get_kapitalis_pages(3)#1656
    kapitalis_ads_links = get_kapitalis_articles_links(kapitalis_pages_links)
    articles_dataset = scrape_kapitalis(kapitalis_ads_links)
    logging.info(f"Number of articles : {len(kapitalis_ads_links)}")
    logging.info(kapitalis_ads_links)
    logging.info(f"articles scraping RESULTS :  {articles_dataset}")
    logging.info(f"NUMBER OF ARTICLES {len(articles_dataset)}")
    file_name = "kapitalis_articles.json"

    # Serialize the data to a JSON-formatted string
    json_data = json.dumps(articles_dataset, default=str)

    # Write the JSON data to the file
    with open(file_name, "w", encoding="UTF-8") as json_file:
        json_file.write(json_data)

    logging.info(f"JSON data has been saved to {file_name}")
