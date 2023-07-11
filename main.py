from utils.helper import DataBuilder, DataReader
from utils.consts import ceps
from seton import SETON


if __name__ == "__main__":

    name_website = "SETON"
    informant_code = "79493"
    DELAY = -9
    #----
    data_reader = DataReader(delay=DELAY)
    path_creator = data_reader.create_folder()
    sheet = data_reader.read_table(informant_code=informant_code, delay=DELAY)
    #----
    collect = SETON()
    collect.scraper(sheet)
    sheet = collect.generate_dateset(sheet)
    #----
    carga_creator = DataBuilder(delay=DELAY).load_creator(
        sheet=sheet, name_website=name_website, informant_code=informant_code
    )
