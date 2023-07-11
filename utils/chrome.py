from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium import webdriver


class Chrome(webdriver.Chrome):
    def __init__(
        self,
        options: list = [
            "window-size=1920,1080",
            "incognito",
            "disable-cache",
            "delete-cookies",
            "headless",
        ],
    ) -> None:
        self.options = webdriver.ChromeOptions()
        self.servico = Service(ChromeDriverManager().install())

        for arguments in options:
            self.options.add_argument(arguments)

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, *args, **kwargs) -> None:
        self.quit()

    def start(self) -> None:
        super(Chrome, self).__init__(service=self.servico, options=self.options)
