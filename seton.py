from utils.chrome import Chrome
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.consts import DICT_ELEMENTOS, ceps
from selenium.webdriver.common.keys import Keys
from time import sleep
from tqdm import tqdm
import pandas as pd
import re
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("debug_seton.log"), logging.StreamHandler()],
)


class SETON:
    def __init__(self) -> None:
        self.prices = []
        self.shipments = []
        self.driver = Chrome()
        self.date = datetime.now()

    def _check_cart(self):
        """The website, even in anonymous mode, somehow appears to store items that have already been added to
        the cartd. I used try and except to ensure that the cart will be emptied."""

        # try:
        #     self.driver.get("https://www.seton.com.br/checkout/cart/")
        #     delete_item = WebDriverWait(self.driver, 3).until(
        #         EC.element_to_be_clickable(
        #             (By.CSS_SELECTOR, DICT_ELEMENTOS["delete_item"])
        #         )
        #     )
        #     delete_item.click()
        # except:
        #     logging.info("The cart is already empty.")

        # accepting all cookies
        #self.driver.get("https://www.seton.com.br/checkout/cart/")
        cookies = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, DICT_ELEMENTOS["cookies"]))
        )
        cookies.click()

    def _add_cart(self):
        try:
            element_add = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, DICT_ELEMENTOS["buy_button"])
                )
            )
            element_add.click()
            self.driver.get("https://www.seton.com.br/checkout/cart/")
        except Exception as e:
            logging.error("Item unavailable.")

    def _change_quantity(self, sheet: pd.DataFrame, i: int):
        sleep(2)
        sheet["QT_MED_INSUMO"] = sheet["QT_MED_INSUMO"].fillna("1")
        amount = int(sheet["QT_MED_INSUMO"][i])
        logging.info(f"Requesting amount: {amount}")

        for c in range(amount - 1):
            try:
                change_amount = self.driver.find_element(
                    By.CSS_SELECTOR, DICT_ELEMENTOS["change_amount"]
                )
                change_amount.click()
                sleep(3.5)

                error_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, ".error-msg"
                )
                if error_elements:
                    logging.info("Error element 'out of stock' found. Breaking the loop.")
                    break

            except:
                logging.info(
                    "The amount does not need to be changed. Click interaction canceled."
                )

        sleep(2)

    def _choose_item(self):
        try:
            input_box = self.driver.find_elements(
                By.CSS_SELECTOR, DICT_ELEMENTOS["item_option"]
            )

            for e in input_box:
                e.click()
                for c in range(2):
                    e.send_keys(Keys.ARROW_DOWN)

                e.click()
        except:
            logging.info("Current URL does not have size selection.")

    # def _return_values(self, css_element: str, SHIP=False):

    #     """If the 'out of stock' element appers on the screen, the value of 'regex'(or 'catch') will be None."""

    #     if SHIP:
    #         try:
    #             error_elements = self.driver.find_element(By.CSS_SELECTOR, ".error-msg")
    #             if error_elements:
    #                 catch = None
    #                 logging.error("Item out of stock.")
    #         except:

    #             shipping_form = self.driver.find_elements(By.CSS_SELECTOR, css_element)
    #             for e in shipping_form:
    #                 e = e.text
    #                 regex = re.compile(r'(PAC - .*|SEDEX - .*|PAC GF - .*)')
    #                 catch = list(re.findall(regex, e))[0]
    #                 catch = catch.split('R$')[-1]

    #         return catch

    #     else:
    #         try:
    #             error_elements = self.driver.find_element(By.CSS_SELECTOR, ".error-msg")

    #             if error_elements:
    #                 regex = None
    #                 logging.error("Item out of stock.")

    #         except:
    #             element_ = (
    #                 WebDriverWait(self.driver, 10)
    #                 .until(EC.presence_of_element_located((By.CSS_SELECTOR, css_element)))
    #                 .text
    #             )
    #             regex = re.findall("R\$(.+,[0-9]+)", element_)[-1]

    #         return regex

    def _return_values(self, css_element: str, SHIP=False):
        """If the 'out of stock' element appears on the screen, the value of 'regex' (or 'catch') will be None."""
        try:
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, ".error-msg")
        except:
            logging.info("The 'out of stock' element is not present on the page.")

        if error_elements:
            logging.error("Item out of stock.")
            catch = None
        else:
            if SHIP:
                shipping_form = self.driver.find_elements(By.CSS_SELECTOR, css_element)
                for e in shipping_form:
                    e = e.text
                    regex = re.compile(r'(PAC - .*|SEDEX - .*|PAC GF - .*|JAMEF - .*)')
                    catch = list(re.findall(regex, e))[0]
                    catch = catch.split('R$')[-1]
            else:
                element_ = (
                    WebDriverWait(self.driver, 10)
                    .until(EC.presence_of_element_located((By.CSS_SELECTOR, css_element)))
                    .text
                )
                regex = re.findall("R\$(.+,[0-9]+)", element_)[-1]
                catch = regex

        return catch


    def _insert_cep(self, sheet: pd.DataFrame, ceps: str, i: int):
        uf = sheet["CD_UF_REGIAO"][i]
        cep = ceps[uf]

        input_cep = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, DICT_ELEMENTOS["input_cep"])
            )
        )
        input_cep.send_keys(cep)

        confirm_button = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, DICT_ELEMENTOS["confirm_button"])
            )
        )
        confirm_button.click()

        sleep(2)

    def _take_screenshot(self, cod_insumo: str, folder_prints: str = "prints"):
        """Function that will take a screenshot of each url in website
        1) "cod_insumo": refers to informant code within the spreedsheet.
        2) "folder_prints": It's the name of my folder where my screenshot will be saved.
        """

        logging.info("Taking screenshot")
        dir_caminho = (
            os.path.abspath(folder_prints)
            + f'\\{cod_insumo}_{self.date.strftime("%d_%m_%Y")}.png'
        )
        self.driver.save_screenshot(dir_caminho)
        sleep(0.6)

    def scraper(self, sheet: pd.DataFrame):
        for i in tqdm(sheet.index):
            try:
                self.driver.start()
                self.driver.get(sheet["URL DO INSUMO"][i])
                logging.info(f"Requesting URL: {self.driver.current_url}")
                #self._check_cart()
                self._choose_item()
                self._add_cart()
                self._change_quantity(sheet, i)
                self._insert_cep(sheet, ceps, i)
                price = self._return_values(DICT_ELEMENTOS["price"])
                shipment = self._return_values(DICT_ELEMENTOS["shipment"], SHIP=True)
            except:
                price, shipment = None, None

            self._take_screenshot(sheet["NR_SEQ_INSINF"][i])

            logging.info(f"Price: {price}")
            logging.info(f"Shipment: {shipment}")

            self.prices.append(price)
            self.shipments.append(shipment)

            self.driver.__exit__()

    def generate_dateset(self, sheet: pd.DataFrame):
        sheet["preco_coleta"] = self.prices
        sheet["frete_coleta"] = self.shipments

        return sheet
