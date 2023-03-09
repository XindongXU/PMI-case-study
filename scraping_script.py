import re
import time
import requests
import pickle
import pandas as pd
import numpy  as np

from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup


def init_checkpoint(Flag = True):
    """
    Function that determine whether to initialize the checkpoints of this scraping scripts,
    or to pass and to continue scraping the product data where the script stop last time.
    
    Parameters:
        Flag    (bool): if True, we are running a new scraping mission, 
                        create two new checkpoint files under certain path: ./data,
                        containing the name and information of products which will have already been visited.
                        
                        else, we will continue the scraping mission where the script stop last time.
        
    Returns:

    """
    if Flag:
        product_dict_list = []
        visited_product = []
        visited_product.append(0)

        with open("./data/visited_product", "wb") as f:
            pickle.dump(visited_product, f)
        with open('./data/visited_product_dict', 'wb') as f:
            pickle.dump(product_dict_list, f)
    else:
        pass


def date_cat(x):
    """
    Function that categorize the time of comments in the review dataframe.
    
    Parameters:
        x   (str):  Time information when the comment is written.
        
    Returns:
        cat (str):  Category according to how long ago the comment is written.
    """
    if x.split()[-1] == 'years':
        cat = 'Longer than 1 year'
    elif x.split()[-1] in ['year', 'months'] and int(x.split()[0]) >= 5:
        cat = '5 months to 1 year ago'
    elif x.split()[-1] == 'months' and int(x.split()[0]) >= 3:
        cat = '3 months to 5 months ago'
    else:
        cat = 'Less than 2 months'
    return cat


def scrape_product_info():
    """
    Fonction that extract information of all the disposable vape product listed on the certain website.

    The script will first browse and save all the products on this page that need to be scraped, and save them in `products`.

    Then a loop will be run:
    At the beginnig of each loop, the script will check if the next product to be scraped can already be found in the 
    checkpoint `visited_product`.
    If not, each time, one product's general information will be saved in a temporary dictionary: `visited_product_dict`.
    The general information for one product contains the brand, name, capacity per stick, nicotine content per 100mL, 
    number of puffs per stick, price, number of review given by customers, average score, recommendation percentage, 
    average scores for the three main attributes: flavor, sweetness and long lasting, and the link to the detailed page.
    After that, the customers' reviews will be collected and saved by `scrape_product_review()`.
    At the end of each loop, this product will be noted in the checkpoint file `visited_product`.

    Finally, the script will try to find if there is a next page of products to be scraped.

    Parameters:

    Returns:

    """

    # The URL of the target webpage
    url_origin = 'https://www.huffandpuffers.com/'
    url_disposable = '/collections/disposable-salt-nicotine-devices'

    # Send a GET request to the webpage
    # Set the product sorting order to be best-selling
    url = url_origin + url_disposable + '?sort_by=best-selling'
    try:
        response = requests.get(url = url)
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        print("Maybe retry later")
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        print("Error of url")
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Set the maximum number of products on one page
    page_max = len(soup.find_all('product-item'))
    page_id  = 0

    while url:
        # Send a GET request to the webpage
        # Parse the HTML content using BeautifulSoup
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all the product listings on the webpage
        products = soup.find_all('product-item')

        # A loop to scrape all the products in product list
        for product_id, product in enumerate(products):

            # Load the checkpoint files
            with open("./data/visited_product", "rb") as f:
                visited_product = pickle.load(f)
            with open("./data/visited_product_dict", "rb") as f:
                product_dict_list = pickle.load(f)

            print("Current page id: ", page_id/30)
            print("Current product id to be scraped : ", product_id)
            print("Latest product id ve been scraped: ", visited_product[-1])
            
            # Check if the next product to be scraped can already be found in `visited_product`.
            if (visited_product.count(0) - 1)*page_max > page_id:
                print('Current page has been scraped, jumping to next page.')
                break
            elif product_id < visited_product[-1]:
                print('Current product has been scraped, jumping to the next one.')
                continue
            
            # Product's general information is stored in the containner 'product-item-meta'
            product_meta = product.find('div', class_='product-item-meta')

            # Extract the product's name, link for details, price, ratings, and nb of puffs
            link = url_origin + product_meta.find('a', class_='product-item-meta__title')['href'].strip()
            name = product_meta.find('a', class_='product-item-meta__title').text.strip()
            nico = re.findall(r"\d+\.?\d*\%", name)[0][:-1] if len(re.findall(r"\d+\.?\d*\%", name)) else 0
            brand = name.split()[0]
            flavor_tags = product_meta.find('div', class_='flavor-tags')
            puffs = int(re.findall(r"\d+", flavor_tags.text.strip())[0])

            # Extract the review total number, the scoring information and the price
            review_summary = product_meta.find('div', class_='okeReviews-reviewsSummary')
            review_info = review_summary.find('span', {'aria-hidden': 'true'}).text.strip() if review_summary else None
            review_count = int(re.findall(r"\d+", review_info)[0]) if review_summary else 0
            
            score_info = review_summary.find('span', class_='okeReviews-a11yText').text.strip() if review_summary else None
            score = float(re.findall(r"\d+\.?\d*", score_info)[0]) if review_summary else None
            price = product_meta.find('div', class_ = "product-item-meta__price-list-container").find('span', class_ = "price").text
            price = float(re.findall(r"\d+\.?\d*", price)[0])

            # Collect and save customers' reviews
            capacity, recommend_agg, flavor, sweet, longl = scrape_product_review(url = link, product_id = product_id + page_id + 1)
            # Capacity per vape, average score for recommendation, flavor, sweetness and long lasting, 
            # are stored in the detailed page and need to be accessed by scrape_product_review()

            product_dict = {
                'Brand':        brand,
                'Name':         name,
                'Capacity(mL)': capacity,
                'Nicotine(%)':  nico,
                'Puffs':        puffs,
                'Price($)':     price,
                'Review_count': review_count,
                'Score':        score,
                'Recommend(%)': recommend_agg,
                'Flavor':       flavor,
                'Sweet':        sweet,
                'Lasting':      longl,
                'Link':         link,
            }

            # Renew the visited product list and their info dictionary
            product_dict_list.append(product_dict)
            visited_product.append(0) if product_id == 29 else visited_product.append(product_id + 1)

            # Save these two files as checkpoints of this script
            with open("./data/visited_product", "wb") as f:
                pickle.dump(visited_product, f)
            with open('./data/visited_product_dict', 'wb') as f:
                pickle.dump(product_dict_list, f)


        # Find the next page button and update the URL
        next_button = soup.find(lambda tag: tag.name == 'a' and tag.get('class') == ['pagination__nav-item'])

        if (next_button and next_button['aria-label'] == 'Next'):
            url = url_origin + next_button['href']
            page_id += page_max
        else :
            break

    return()

def scrape_product_review(url, product_id):
    """
    Fonction that extract review information in the given detailed webpage, and save it in a csv sheet.
    By using `selenium`, the script will first click all the 'show more' button on the page, and collect all the review contents.

    Parameters:
        url         (str):      Link to the product's detailed information webpage.
        product_id  (int):      The index number of the current product.

    Returns:
        capacity    (float):    Capacity per stick.
        recommend   (float):    Total recommendation percentage.
        flavor      (float):    Average scores for the product's flavor.
        sweet       (float):    Average scores for the product's sweetness.
        longl       (float):    Average scores for the product's long-lasting.
    """

    # Set a chrome webdriver to interact with the webpage
    option = ChromeOptions()
    option.add_experimental_option('excludeSwitches', ['enable-logging'])
    option.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=option)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'})
    driver.get(url = url)

    # Click all the 'show more' button on the page to obtain the full review data
    while True:
        try:
            show_more_button = WebDriverWait(driver, 25).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.okeReviews-reviews-showMore')))
            show_more_button.click()
        except (TimeoutException, ElementNotInteractableException):
            break

    # Extract product capacity
    descrpt = driver.find_element(By.XPATH,
            '//*[@class="product-tabs__tab-item-content rte"]/ul[1]').text
    capacity = re.findall(r"\d+\.?\d+\s?mL", descrpt)[0] if len(re.findall(r"\d+\.?\d+\s?mL", descrpt)) else None
    capacity = float(re.findall(r"\d+\.?\d+", capacity)[0]) if len(re.findall(r"\d+\.?\d+\s?mL", descrpt)) else None
    
    # Extract product aggregate recommemdation percentage, flavor score, sweetness score, and long lasting score
    recommend = driver.find_element(By.XPATH,
        '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]').text if driver.find_elements(By.XPATH,
        '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    flavor_agg = driver.find_element(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[2]/div[1]/table/tbody/tr[1]/td[2]/div[1]/div[1]/div[1]').get_attribute('style') if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    flavor = float(re.findall(r"\d+\.?\d+", flavor_agg)[0]) if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    sweet_agg = driver.find_element(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[2]/div[1]/table/tbody/tr[2]/td[2]/div[1]/div[1]/div[1]').get_attribute('style') if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    sweet = float(re.findall(r"\d+\.?\d+", sweet_agg)[0]) if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    longl_agg = driver.find_element(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[2]/div[1]/table/tbody/tr[3]/td[2]/div[1]/div[1]/div[1]').get_attribute('style') if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None
    longl = float(re.findall(r"\d+\.?\d+", longl_agg)[0]) if driver.find_elements(By.XPATH,
            '//*[@class="okeReviews-reviewsAggregate-primary"]/div[1]/span[1]') else None

    # Extract all review, including the rating, head text, content, date, and scores to the three attribute
    review_ratings = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[1]/div[1]/div[1]/span[1]')

    review_dates = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[1]/div[2]/span[2]')
    
    review_heads = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[2]/h2')

    review_texts = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[2]/div[1]/div[1]')

    review_attributes_1 = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[3]/table/tbody/tr[1]/td/div/span')

    review_attributes_2 = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[3]/table/tbody/tr[2]/td/div/span')

    review_attributes_3 = driver.find_elements(By.XPATH,
                '//*[@class="okeReviews-reviews-review"]/article[1]/div[2]/div[3]/table/tbody/tr[3]/td/div/span')
    
    # Notice that the reviews older that 5 months ago don't have the score to the three attribute
    # Pad the attribute score with None, prepare them for the dataframe
    review_attributes_1 += [None]*(len(review_ratings)-len(review_attributes_1))
    review_attributes_2 += [None]*(len(review_ratings)-len(review_attributes_2))
    review_attributes_3 += [None]*(len(review_ratings)-len(review_attributes_3))

    # Dataset of all reviews under the current product
    df_review = pd.DataFrame({  'Ratings' : review_ratings,
                                'Dates'   : review_dates,
                                'Heads'   : review_heads,
                                'Texts'   : review_texts,
                                'Flavor'  : review_attributes_1,
                                'Sweet'   : review_attributes_2,
                                'Lasting' : review_attributes_3,},
                                columns = ['Ratings', 'Dates', 'Heads', 'Texts', 'Flavor', 'Sweet', 'Lasting'])
    
    if len(df_review):
        # Extract the rating info from the web element text, and set its data type to float
        df_review['Ratings'] = df_review['Ratings'].apply(lambda x: x.text)
        df_review['Ratings'] = df_review['Ratings'].str.extract(r'(\d+[.\d]*)')
        df_review['Ratings'] = df_review['Ratings'].astype(float)
        
        # Extract the date info from the web element text, and set its data type to string, and categorize it by date_cat()
        df_review['Dates'] = df_review['Dates'].apply(lambda x: x.text)
        df_review['Dates'] = df_review['Dates'].str.extract(
                        r'(\d+\s+(seconds|second|minutes|minute|hours|hour|days|day|months|month|years|year))').loc[:,0]
        df_review['Date_Category'] = df_review['Dates'].apply(lambda x : date_cat(x))
        
        # Extract the head and text info from the web element texts, and set their data type to string
        df_review['Heads'] = df_review['Heads'].apply(lambda x: x.text)
        df_review['Texts'] = df_review['Texts'].apply(lambda x: x.text)

        # Extract the attributes' scores from the web element texts, and set their data type to float
        df_review['Flavor'] = df_review['Flavor'].apply(lambda x: x.text if x else None)
        df_review['Flavor'] = df_review['Flavor'].str.extract(r'(\d+[.\d]*)')
        df_review['Flavor'] = df_review['Flavor'].astype(float)
        df_review['Sweet'] = df_review['Sweet'].apply(lambda x: x.text if x else None)
        df_review['Sweet'] = df_review['Sweet'].str.extract(r'(\d+[.\d]*)')
        df_review['Sweet'] = df_review['Sweet'].astype(float)
        df_review['Lasting'] = df_review['Lasting'].apply(lambda x: x.text if x else None)
        df_review['Lasting'] = df_review['Lasting'].str.extract(r'(\d+[.\d]*)')
        df_review['Lasting'] = df_review['Lasting'].astype(float)

    # Reindex the dataframe, save it in form of csv sheet and name it by the product_id
    df_review = pd.DataFrame(df_review, 
                            columns = ['Ratings', 'Dates', 'Date_Category', 'Heads', 'Texts', 'Flavor', 'Sweet', 'Lasting'])
    df_review.index += 1
    df_review.index.names = ['Review_id']
    df_review.to_csv('./data/df_review_{product_id}.csv'.format(product_id = product_id), index=True)

    # Quit the selenium chrome driver
    driver.quit()

    return(capacity, recommend, flavor, sweet, longl)


if __name__ == '__main__':
    # Initialize the scraping mission and the checkpoints files, by setting the parameter to True
    # Continue the last time scraping mission and start from the checkpoint, by setting the parameter to False
    init_checkpoint(Flag = True)

    # Run the scraping mission
    scrape_product_info()

    # Load the saved dictionary list of the visited product data
    with open("./data/visited_product_dict", "rb") as f:
        product_dict_list = pickle.load(f)

    # Create and save the dataframe based on the dictionary list
    df_info = pd.DataFrame(product_dict_list)
    df_info.index += 1
    df_info.index.names = ['Product_id']
    
    df_info.to_csv('./data/df_info.csv', index=True)
    df_info = pd.read_csv('./data/df_info.csv', index_col = 'Product_id')
    print(df_info.head(5))