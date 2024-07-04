import time
import zipfile
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from fake_useragent import UserAgent

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


PROXY_HOST = ''
PROXY_PORT = '' 
PROXY_USER = ''
PROXY_PASS = '' 

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""

background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
        singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
        }
    };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

useragent = UserAgent()

options = webdriver.ChromeOptions()



def get_chromedriver(use_proxy=False, user_agent=useragent.random):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920x1080")
    # chrome_options.add_experimental_option("prefs", {
    #     "profile.managed_default_content_settings.javascript": 2
    # })
    if use_proxy:
        # chrome_options.add_argument('--proxy-server=196.17.64.149:8000')
        plugin_file = 'proxy_auth_plugin.zip'

        with zipfile.ZipFile(plugin_file, 'w') as zp:
            zp.writestr('manifest.json', manifest_json)
            zp.writestr('background.js', background_js)

        chrome_options.add_extension(plugin_file)

    if user_agent:
        chrome_options.add_argument(f'--user-agent={user_agent}')

    driver = webdriver.Chrome(options=chrome_options)

    return driver


def main():
        browser = get_chromedriver(use_proxy=False)
        browser.get("https://kad.arbitr.ru/Version/Change?mode=Full&returnUrl=%2F")
        time.sleep(8)
    # try:
        
        browser.find_element(By.CSS_SELECTOR, '[placeholder="название, ИНН или ОГРН"]').send_keys("Федоров Никита Артурович")

        button = WebDriverWait(browser, 2).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'b-button-container'))
        )
        button.click()

        time.sleep(3)

        path_link = str("//*[@class= 'b-cases']/tbody/tr/td/div/a")
        links = browser.find_elements(By.XPATH, path_link)
        urls = []
        for url in links:
            urls.append(url.get_attribute('href'))

        counter = 0

        for url in urls:
            counter += 1
            print(f"{counter} дело из {len(urls)} дел")
            browser.get(url)
            time.sleep(3)

            # Поиск элемента и щелчок по нему
            icon = browser.find_element(By.CSS_SELECTOR, ".b-sicon")
            icon.click()

            # Ожидание завершения загрузки
            wait = WebDriverWait(browser, 10)
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".js-sicon--loading")))



            time.sleep(5)
            page_data = browser.page_source

            soup = BeautifulSoup(page_data, "html.parser")
            full_result = []

            headers = soup.find_all("div", class_="b-chrono-item-header")
            container = soup.find_all("div", class_="b-chrono-items-container")

            for head in headers:
                head_title = head.find("strong").text.strip()
                head_date = head.find("span", class_="b-reg-date").text.strip()
                head_instance = ' '.join(head.find("h4", class_="b-case-instance").text.split())
                try:
                    head_resolution = head.find("h2", class_="b-case-result").text.strip()
                except:
                    head_resolution = None
                result_containers = []

                for div in container:
                    cases = div.find_all("div", class_="b-chrono-item")
                    for case in cases:

                        case_type = case.find('p', class_="case-type").text.strip()
                        case_date = case.find('p', class_="case-date").text.strip()
                        case_subject = case.find('p', class_="case-subject js-case-subject").text.split()
                        case_subject = ' '.join(case_subject)
                        case_resolution = case.find("span", class_="js-judges-rollover").text.strip()
                        try:
                            case_resolution_date = case.find("p", class_="b-case-publish_info js-case-publish_info").text.strip()
                        except:
                            case_resolution_date = None


                        result_container = {
                            "step_name": case_type,
                            "step_date": case_date,
                            "step_resolution": case_resolution,
                            "step_resolution_date": case_resolution_date,
                            "step_subject": case_subject,
                        }
                    
                        result_containers.append(result_container)
                
                
                    res = {
                        head_title: {
                            head_date: {
                            "resolution": head_resolution,
                            "court": head_instance,
                            "chronology": result_containers
                    
                            }
                        }
                        }

                full_result.append(res)


            with open(f'case_{counter}.json', 'w', encoding='utf-8') as file:
                json.dump(full_result, file, ensure_ascii=False, indent=4)  



    # except Exception as e:
    #     print(e)

        time.sleep(2)
        browser.close()


if __name__ == "__main__":
    main()
