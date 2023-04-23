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


def load_csv(file_name="out"):
    try:
        file_name += '.csv'
        return pd.read_csv(DATA_PATH + file_name, index_col=[0])

    except FileNotFoundError:
        print("Arquivo [" + file_name + "] nao encontrado!")


def write_csv(dataframe, name='employers-out'):
    # Grava csv com nome dado ou employers-out.csv por padrao
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


def get_values(raw_value):
    value = []
    string_value = re.findall("USD\s*(\d{1,3}(?:,\d{2})*(?:\.\d{2})?)", raw_value)
    if string_value:
        dotted_value = [x.replace(',', '.') for x in string_value]
        value = [float(x) for x in dotted_value]
        value.sort()
    return value


def clean_income(raw_income):
    output = []
    income = get_values(raw_income)

    if sanitize(raw_income).find(sanitize('tips')) != -1:
        output.append(raw_income)
    elif len(income) == 1:
        output.append(income[-1])
    elif len(income) > 1:
        average = sum(income) / len(income)
        output.append(income)
        output.append((income[0] + average) / 2)
        return output

    if income:
        output.append(income[-1])
        return output

    return output, None


def get_income(text):
    if len(text) > 18 and sanitize(text[:18]) == sanitize('Média de salário: '):
        return clean_income(text[18:])


def weekly_price_converter(raw_housing, value):
    if sanitize(raw_housing).find(sanitize('por mês')) != -1:
        return value[-1]/4
    return value[-1]


def clean_housing(raw_housing):
    output = []
    string_housing = re.findall("USD\s*\d{1,3}(?:,\d{2})*(?:\.\d{2})?[\w\W]*", raw_housing)
    housing = get_values(raw_housing)

    if sanitize(raw_housing).find(sanitize('Não é oferecida pelo empregador')) != -1:
        output.append(raw_housing)
    elif len(housing) >= 1:
        output.append(string_housing)

    if len(housing) >= 1:
        output.append(weekly_price_converter(raw_housing, housing))
        return output

    return output, None


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
                for entry in income:
                    employer_data[counter].append(entry)
            elif housing:
                for entry in housing:
                    employer_data[counter].append(entry)
        employer_data[counter].append(get_taxes(employer_data[counter][2]))
        counter += 1

    return employer_data


def get_taxes(state):
    taxes = load_csv('us_taxes_2023_table').to_dict()
    return float(taxes['Combined Rate'][state.upper()].replace('%','')) + float(taxes['Combined Rate']['US'].replace('%',''))


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

        for employer in range(len(employers)):
            employers[employer].append([])
            employers[employer].append(400)

        for i in employers:
            print(i)

        new_data = pd.DataFrame(employers, columns=['name', 'place', 'state', 'payrate', 'ex pay', 'housing', 'ex housing', 'taxes', 'job offer', 'living cost'])

        write_csv(new_data)


main()
