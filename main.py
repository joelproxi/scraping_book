import csv
import os
import shutil
import requests

from typing import Optional
import pandas as pd
from bs4 import BeautifulSoup


path = os.getcwd()

BASE_URL = 'http://books.toscrape.com/'



def get_page(url: str) -> BeautifulSoup:
    soup = None
    try:     
        page = requests.get(url)
        if page.ok:
            soup = BeautifulSoup(page.content, 'html.parser')
    except requests.ConnectionError:
        print('Connexion Error ')
    except requests.Timeout:
        print('Coonexion time out')
    return soup

def get_category_links(url: str) -> set:
    soup = get_page(url=url)
    achors = soup.find('ul', attrs={'class': 'nav nav-list'}).ul.find_all('a')
    link_list: list = [(BASE_URL+link['href']) for link in achors]
    # print(link_list)
    return set(link_list)

def get_books_link_by_category(url: str) -> tuple[set, str]:
    soup = get_page(url=url)
    category: str = soup.find('div', attrs={'class': "page-header action"}).h1.text.strip().lower()
    ol = soup.find('ol', attrs={'class': 'row'}).find_all('a')
    book_links = [ (BASE_URL + 'catalogue/' + link['href'][9:]) for link in ol ]
    # print(len(book_links))
    header = ['product_page_url',
            'universal_ product_code (upc)',
            'title',
            'price_including_tax',
            'price_excluding_tax',
            'number_available',
            'product_description',
            'category',
            'review_rating',
            'image_url'
    ]
    
    try: 
        os.makedirs(f'data/images/{category}')
    except FileExistsError:
        pass
    
    create_read_csv(category,  data=header, mode='w')
    print(f'+++++++++++++++++{category}+++++++++++++++++++++++')    
    return set(book_links), category  
       
def extra_book_info(url, category_name):
    soup: BeautifulSoup = get_page(url=url)
    table = soup.find('table')
    product_page_url = BASE_URL
    universal_product_code  =  table.find(text='UPC').next_element.text
    title = soup.find('div',attrs={ "class": "col-sm-6 product_main"}).h1.text
    price_including_tax =  table.find(text='Price (incl. tax)').next_element.text.replace('£', '')
    price_excluding_tax = table.find(text='Price (excl. tax)').next_element.text.replace('£', '')
    number_available = table.find(text='Availability').next_element.next.text.replace('In stock (', '').replace(' available)', '')
    product_description = soup.find('meta', attrs={'name': 'description'})['content'].strip()
    category = soup.find('ul',attrs={ "class": "breadcrumb"}).find_all('a')[-2]
    category = category.text.strip().lower()
    review_rating = table.find(text='Number of reviews').next_element.next.text
    image_url = BASE_URL + soup.find('img')['src'][6:]
    
    data = [
        product_page_url,
        universal_product_code,
        title,
        price_including_tax,
        price_excluding_tax,
        number_available,
        product_description,
        category,
        review_rating,
        image_url
    ]
    # print(data)
    create_read_csv(category_name, data=data, mode='a')
    download_image(category_name, title, image_url)
    print(f"_________________Extraction de {title[:15]} ___________________")


def create_read_csv(file_name: str,  data=None, mode=None):
    file: str = 'data/csv/{}.csv'.format(file_name)
    with open(file, mode, newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(data)

def download_image(category_name: str, file_name: str, file_url: str):
    req = requests.get(file_url, stream=True)
    if req.status_code == 200:
        req.raw.decode_content = True
        file = file_name.lower().replace(' ', '').replace(',', '').replace('.', '').replace("'", '').replace(':', '').replace('?', '')
        file = file.replace('#', '').replace('<','').replace(')','').replace('>','').replace('~','').replace('"', '').replace('/', '')
        file = file.replace('@', '').replace('&','').replace('*','').replace('(','').replace('_','').replace('-', '').replace('|').rstrip()
        with open(f'data/images/{category_name}/{file}', 'wb') as f:
            shutil.copyfileobj(req.raw, f)
        print('Telechargment de limage %s' % file_name)

def main(url: str):
    try:
        os.makedirs('data/csv')
        os.makedirs('data/images')
    except FileExistsError:
        pass
    
    category_link_list: set = get_category_links(url=url)
    for cat_link in category_link_list:
        book_links_list, category_name =  get_books_link_by_category(cat_link)
        for book_link in book_links_list:
            extra_book_info(book_link, category_name)
    
      
main(BASE_URL)

