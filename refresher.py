import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

URL = "https://www.travelmate.com.br/empregadores-worktravel/"
DATA_PATH = ""
WAIT_SECONDS = 15


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
        return pd.read_csv(DATA_PATH + file_name)

    except FileNotFoundError:
        print("Arquivo [" + file_name + "] nao encontrado!")
        print("Um novo arquivo sera criado!")


def write_csv(dataframe, name='out'):
    # Grava csv com nome dado ou out.csv por padrao
    filename = name + '.csv'
    dataframe.to_csv(DATA_PATH + filename)
    print("Arquivo salvo com nome " + filename)


def main():
    output_data = load_csv()
    html = load_file()

    if html:
        soup = BeautifulSoup(html, features="html.parser")

        results = soup.find_all("div", {"class": "sessao-estado"})
        estado = []

        for result in results:
            # print(result.prettify(), end="\n")

            state_sigle = result.get('id')[7:]
            # estado[state_sigle] = []
            # print(state_sigle)
            for i in result.find_all('a', class_="link-verde"):
                link = i.get('href')
                title_start = link.rfind("/") + 1
                title_end = link.rfind(".")
                title = link[title_start:title_end]
                # print(title)
                now = datetime.today().strftime('%Y-%m-%d %H:%M')
                estado.append((state_sigle, title, now, link, 0))

            # employer_cities = result.find_all('p', class_="cidade-empregador")
            # positions = []

            # for employer in result.find_all("div", class_="tm-card-custom-list-requisitos"):
            #    specific_info = employer.find_all("li")
            #    positions.append(specific_info[1])
            #    print(specific_info[1])
            # city_counter = 0
            # employer_dict = {}

            # for employer in result.find_all('h2'):
            #    employer_location = employer.string + " - " + employer_cities[city_counter].contents[0]
            #    city_counter += 1
            #    employer_dict[employer_location] = city_counter

            # estado[state_sigle] = employer_dict

        opened_file = output_data.link.to_list()
        new_data = pd.DataFrame(estado, columns=['estado', 'titulo', 'data_add', 'link', 'status'])
        downloaded_data = new_data.link.to_list()

        diff = False

        print("Empregadores atualizados:")

        for link in downloaded_data:
            if link not in opened_file:
                diff = True
                print(link)

        if diff:
            write_csv(new_data)
        else:
            print("Sem atualização de empregadores!")


main()
