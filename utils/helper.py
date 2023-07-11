import pandas as pd
import os
import numpy as np
from utils.consts import MESES, RENAME_COLUMNS, REORDER_LIST, INPUT_TABLE
from calendar import isleap
from datetime import datetime
from datetime import timedelta


class DataReader:
    def __init__(self, delay) -> datetime:
        self.date = datetime.now() - timedelta(delay)


    def folder(self, nome_pasta: str):
        '''Function responsable for creating folder
            1) "nome_pasta": It's the name of folder. '''
        try:
            # Converte o nome da pasta em uma string, caso ainda não seja uma
            nome_pasta = str(nome_pasta)
            # Cria o caminho completo da pasta, concatenando o diretório atual com o nome da pasta
            dir_destino = os.path.join(os.getcwd(), nome_pasta)
            # Verifica se a pasta já existe, se não existir, cria a pasta
            if not os.path.exists(dir_destino):
                # Cria a pasta com o nome especificado
                os.makedirs(dir_destino)
            # Navega para a pasta criada
            os.chdir(dir_destino)
            # Exibe mensagem de sucesso
            print(f"Foi para a pasta {nome_pasta}")
        except OSError as e:
            # Exibe mensagem de erro caso não seja possível criar a pasta
            print(f"Não foi possível criar a pasta {nome_pasta}: {e}")

    def create_folder(self, folder_prints:str = "prints"):
        '''Cria as pastas necessárias para armazenar os arquivos da coleta e saída'''
        dt_prev_ini, dt_prev_fim = self.intervalo_datas()
        
        # Cria a pasta coleta_n, onde n é o ano da data prevista
        year_folder = f'coleta_{self.date.year}'
        self.folder(year_folder)

        # Cria a pasta coleta_mes, onde mes é o mês correspondente à data prevista
        month_folder = f'coleta_{MESES.get(str(self.date.month))}'
        self.folder(month_folder)

        # Cria a pasta do decendio correspondente à data prevista
        decendio = (dt_prev_fim) // 10 
        self.folder(f"coleta_{decendio}_dec")

        # Cria a pasta saida_ano_mes_dia correspondente à data prevista
        self.folder(f"saida_{self.date.strftime('%Y_%m_%d')}")

        try:
            os.mkdir(folder_prints)
        except OSError as e:
            # Exibe mensagem de erro caso não seja possível criar a pasta
            print(f"Não foi possível criar a pasta {folder_prints}: {e}")
        

    def intervalo_datas(self):
        '''The function responsible for returning the interval between the dates within the spreadsheet.'''

        # caso o mês seja fevereiro
        if self.date.month == 2:

            #A função isleap irá verificar se fevereiro está em um ano bissexto. Caso esteja, o mes terá 29 dias ou 28 dias.
            if isleap(self.date.year):
                max_day = 29
            else:
                max_day = 28

        #Os meses Abril, Junho, Setembro e Novembro são meses com 30 dias, logo o máximo será 30 dias.        
        elif self.date.month in {4, 6, 9, 11}:
            max_day = 30

        #O restante dos meses contêm 31 dias em seu total.
        else: 
            max_day = 31

        intervalo = [
            {'ini': 1, 'fim': 10},
            {'ini': 11, 'fim': 20},
            {'ini': 21, 'fim': max_day} #A condicional irá obter a quantidade máxima de dias que aquele mês possui.
        ]

        #retorna o intervalo do dec em que a data está.
        for dec in intervalo:
            if self.date.day <= dec['fim']:
                dt_prev_ini = dec['ini']
                print("Data Prevista inicial: ", dt_prev_ini)
                dt_prev_fim = dec['fim']
                print("Data Prevista final: ", dt_prev_fim)
                break

        return dt_prev_ini, dt_prev_fim
    
    def read_table(self, informant_code:str, delay: int = 0):# = "D:/VSCODE/1_Robos/Pasta Testes"):
        self.date = datetime.now().date() - timedelta(delay)
        print('datetime now', self.date)
        self.dt_prev_ini, self.dt_prev_fim = self.intervalo_datas()
        file = self.date.strftime("encomenda_%Y%m%d.xls")
        #file = "encomenda_20230327.xls"
        sheet = pd.read_csv(f'{INPUT_TABLE}/{file}',
                         delimiter='\t',
                         encoding="ISO-8859-1",
                         dtype={'CD_INFORM': str, 'DATA_PREVISTA': str, 'NR_SEQ_INSINF': str})
        sheet = sheet[sheet.CD_INFORM == informant_code]
        #print(sheet)
        #sheet = sheet[(sheet["CD_PERIOD"] == 'QUINZ') | (sheet["CD_PERIOD"] == 'M10') | (sheet["CD_PERIOD"] == 'DEC')]

         #convertendo a coluna data_prevista para o formato de horas usando o to_datetime
        sheet['DATA_PREVISTA'] = pd.to_datetime(sheet['DATA_PREVISTA'], format='%d/%m/%y', errors='coerce')
        
        #filtrando pelo menos atual
        sheet = sheet[(sheet['DATA_PREVISTA'].dt.month == self.date.month)]
        
        #filtrando para o intervalo de data da função intervalo_datas()
        sheet = sheet[(sheet['DATA_PREVISTA'].dt.day <= self.dt_prev_fim) & (sheet['DATA_PREVISTA'].dt.day > self.dt_prev_ini)]
    
        print(sheet['DATA_PREVISTA'])

        #convertendo de volta a coluna data_prevista para o padrão str
        sheet['DATA_PREVISTA'] = sheet['DATA_PREVISTA'].dt.strftime('%d/%m/%Y')
        print(sheet)
        #sheet['URL DO INSUMO'] = "https://www.ferramentaskennedy.com.br/100040325/arame-de-solda-mig-carretel-em-plstico-08mm-15kg-worker"
        print(sheet.shape)
        
        return sheet


class DataBuilder:

    def __init__(self, delay:int = 0):
        self.date = datetime.today() - timedelta(delay)

    def load_creator(self, sheet, name_website, informant_code) -> pd.DataFrame:

        sheet["data_coleta"] = self.date.strftime('%d/%m/%Y')
        sheet.to_excel("carga_prep_teste.xls")
        sheet = sheet.rename(columns=RENAME_COLUMNS)
        sheet = sheet.reindex(columns=REORDER_LIST)
        sheet = sheet.fillna("")

        print('encomenda', sheet.shape)
        dataframe = sheet[REORDER_LIST].copy()
        print('carga', sheet.shape)
        dataframe['FT'] = np.where(dataframe['Valor do Preço'] == "", "S", "")
        dataframe['Justificativa Livre'] = np.where(dataframe['Valor do Preço'] == '', 'ITEM EM FALTA NO SITE/BOLETIM/TABELA', 'PREÇO CONFORME SITE/BOLETIM/TABELA')
        dataframe['Moeda'] = 'R$'
        dataframe['Valor do Preço'] = dataframe['Valor do Preço'].replace('.', '')
        dataframe['Valor do Frete'] = dataframe['Valor do Frete'].replace('.', '')
        dataframe['Frete Incluso'] = np.where(dataframe['Valor do Frete'] == "0,00", "S", "N")
        dataframe['Frete Incluso'] = np.where(dataframe['Valor do Preço'] == "", "", dataframe['Frete Incluso'])
        dataframe['Data Prevista'] = sheet['Data Prevista']
        file_name = f"carga_{name_website}_BP{informant_code}_{self.date.strftime('%d_%m_%Y')}.xls"        
        dataframe.to_excel(file_name, sheet_name='Carga BP', index=False)
    
        