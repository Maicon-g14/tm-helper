import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import pandas as pd
import re

URL = "https://www.travelmate.com.br/empregadores-worktravel/"
DATA_PATH = ""
WAIT_SECONDS = 5


def write_on_disk(file_to_save, data_path=DATA_PATH):
    try:
        with open(data_path + 'site-data.html', 'w', encoding='utf-8-sig') as file:
            file.write(file_to_save)
        print("Data Saved!")
    except Exception as e:
        print("Couldn't save data!")
        print(e)


def fetch_page(site_url=URL, sleep_time=WAIT_SECONDS):
    print("Will fetch data from: " + site_url)
    service = Service(executable_path=r'G:\PortablePrograms\GeckoDriverPythonSelenium\geckodriver.exe')
    driver = webdriver.Firefox(service=service)
    driver.get(site_url)

    print("Waiting until page loading is finished")
    time.sleep(sleep_time)

    print("Fetching data...")

    webpage = driver.page_source
    driver.quit()

    return webpage


def load_file(data_path=DATA_PATH):
    loaded_file = None
    if data_path:
        print("Loading data from: " + data_path)
    try:
        with open(data_path + 'site-data.html', 'r', encoding='utf-8-sig') as file:
            loaded_file = file.read()
        print("Loaded!")
    except FileNotFoundError:
        loaded_file = fetch_page()
        #write_on_disk(loaded_file)     #ativar pra agilizar debug
    except Exception as e:
        print(e)

    return loaded_file


def write_csv(dataframe, name='out'):
    # Grava csv com nome dado ou out.csv por padrao
    filename = name + '.csv'
    dataframe.to_csv(DATA_PATH + filename)
    print("Arquivo salvo com nome " + filename)


def page_parser(page):
    soup = BeautifulSoup(page, features="html.parser")
    return soup.find_all("div", {"class": "sessao-estado"}) 


def get_state_sigle(page_item):
    return page_item.get('id')[7:]


def get_employer_header(page_item, state_sigle):
    employer_data = []
    for employer_header in page_item.find_all('div', class_="nome-empregador"):
        employer_name = employer_header.findChild('h2').text
        employer_city_raw = employer_header.findChild('p').text
        employer_city_end = employer_city_raw.rfind("(")
        employer_city = employer_city_raw[:employer_city_end]
        employer_data.append([employer_name, employer_city, state_sigle])

    return employer_data


def sanitize(text):
    return text.strip().lower()


def clean_income(raw_income):
    if sanitize(raw_income).find(sanitize('tips')) != -1:
        return raw_income
    income = re.findall("USD\s*(\d{1,3}(?:,\d{2})*(?:\.\d{2})?)", raw_income)
    if income:
        return income
    return []


def get_income(text):
    if len(text) > 18 and sanitize(text[:18]) == sanitize('Média de salário: '):
        return clean_income(text[18:])


def clean_housing(raw_housing):
    if sanitize(raw_housing).find(sanitize('Não é oferecida pelo empregador')) != -1:
        return raw_housing

    housing = re.findall("USD\s*\d{1,3}(?:,\d{2})*(?:\.\d{2})?[\w\W]*", raw_housing)
    if len(housing) == 1:
        return housing[0]

    return housing


def get_housing(text):
    if len(text) > 9 and sanitize(text[:9]) == sanitize('Housing: '):
        return clean_housing(text[9:])


def get_employer_content(page_item, employer_data):
    counter = 0
    for employer_content in page_item.find_all('div', class_="empregador-conteudo"):
        for subject in employer_content.find_all('li'):
            content = subject.text
            income = get_income(content)
            housing = get_housing(content)
            if income:
                employer_data[counter].append(income)
            elif housing:
                employer_data[counter].append(housing)
        counter += 1

    return employer_data


def main():
    page = load_file()

    if page:
        parsed_page = page_parser(page)
        employers = []

        for page_item in parsed_page:
            #print(page_item.prettify(), end="\n")
            state_sigle = get_state_sigle(page_item)
            employer_data = get_employer_header(page_item, state_sigle)
            employers += get_employer_content(page_item, employer_data)

        for i in employers:
            print(i)

        new_data = pd.DataFrame(employers, columns=['nome', 'local', 'estado', 'payrate', 'housing'])

        write_csv(new_data)


main()
