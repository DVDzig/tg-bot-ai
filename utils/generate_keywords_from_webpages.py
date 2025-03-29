import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import logging
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from services.gpt_service import generate_ai_response
from services.google_sheets_service import update_keywords_for_discipline, get_sheet_data

# === НАСТРОЙКА ===
PROGRAM_URLS = {
    "ТПР": "https://d.mgpu.ru/plan/public/task?id=2390",
    "МРК": "https://d.mgpu.ru/plan/public/task?id=2382",
    "БХ": "https://d.mgpu.ru/plan/public/task?id=2386",
}

logging.basicConfig(level=logging.DEBUG)

# === SELENIUM НАСТРОЙКИ ===
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# === ОСНОВНЫЕ ФУНКЦИИ ===
def normalize(text):
    return re.sub(r'\s+', ' ', text.lower().strip())

def extract_text_from_url(url, driver):
    driver.get(url)
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    text = soup.get_text(separator=' ')
    text = ' '.join(text.split())
    return text[:7000]

def generate_keywords_from_text(text, discipline, module):
    prompt = (
        f"Ты — методист. Прочитай текст рабочей программы дисциплины "
        f"«{discipline}» модуля «{module}». На его основе выдели 100–120 ключевых слов или понятий, "
        f"характерных для содержания дисциплины. Только слова и словосочетания, без описаний."
    )
    return generate_ai_response(prompt + "\n\n" + text)

def extract_discipline_links(page_url, driver):
    driver.get(page_url)
    time.sleep(2)

    # Разворачиваем все модули на странице
    toggles = driver.find_elements(By.CLASS_NAME, "accordion-toggle")
    logging.debug(f"Найдено {len(toggles)} элементов .accordion-toggle")
    for t in toggles:
        logging.debug(f"  ➤ Текст: {t.text}")

    for toggle in toggles:
        try:
            ActionChains(driver).move_to_element(toggle).click(toggle).perform()
            time.sleep(0.5)
        except Exception as e:
            logging.warning(f"⚠️ Не удалось кликнуть по модулю: {e}")

    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    disciplines = []

    for block in soup.select(".panel-collapse"):
        module_header = block.find_previous("div", class_="panel-heading")
        module_name = module_header.get_text(strip=True) if module_header else "Модуль"

        for row in block.select("table.table tbody tr"):
            cells = row.find_all("td")
            if not cells:
                continue

            discipline_cell = cells[0]
            link = discipline_cell.find("a")
            if link and "rpd" in link.get("href"):
                href = link.get("href")
                discipline_name = link.get_text(strip=True)
                full_url = "https://d.mgpu.ru" + href if href.startswith("/") else href

                disciplines.append({
                    "module": module_name,
                    "discipline": discipline_name,
                    "url": full_url
                })
                logging.info(f"Найдена дисциплина: {module_name} → {discipline_name} → {full_url}")

    return disciplines

def process_program(program_name, page_url, sheet_name, driver):
    from config import PROGRAM_SHEETS
    logging.info(f"📘 Обрабатываем программу: {program_name}")
    disciplines = extract_discipline_links(page_url, driver)
    logging.debug(f"Найдено дисциплин: {len(disciplines)}")
    for item in disciplines:
        logging.debug(f"  - {item['module']} → {item['discipline']} → {item['url']}")

    sheet_data = get_sheet_data(PROGRAM_SHEETS, f"{sheet_name}!A2:C")

    not_updated = []

    for item in disciplines:
        module = normalize(item["module"])
        discipline = normalize(item["discipline"])
        url = item["url"]

        found = False
        for row in sheet_data:
            if len(row) >= 2:
                sheet_module = normalize(row[0])
                sheet_discipline = normalize(row[1])
                logging.debug(f"→ Сравнение: '{sheet_module}' == '{module}', '{sheet_discipline}' == '{discipline}'")

                if sheet_module == module and sheet_discipline == discipline:
                    found = True
                    try:
                        logging.info(f"🔍 {item['module']} → {item['discipline']}")
                        text = extract_text_from_url(url, driver)
                        keywords = generate_keywords_from_text(text, item['discipline'], item['module'])
                        logging.debug(f"[GPT] Ключевые слова: {keywords[:300]}...")
                        update_keywords_for_discipline(item['module'], item['discipline'], keywords)
                        logging.info("✅ Ключевые слова обновлены")
                    except Exception as e:
                        logging.error(f"❌ Ошибка при обновлении: {item['module']} → {item['discipline']}: {e}")
                        not_updated.append(f"{program_name} → {item['module']} → {item['discipline']}")
                    break

        if not found:
            logging.warning(f"⚠️ Не найдена в таблице: {item['module']} → {item['discipline']}")
            not_updated.append(f"{program_name} → {item['module']} → {item['discipline']}")

    if not_updated:
        logging.info("\n❌ Не удалось обновить ключевые слова для следующих дисциплин:")
        for item in not_updated:
            logging.info(f"- {item}")
    else:
        logging.info("\n✅ Все ключевые слова успешно обновлены!")

# === ЗАПУСК ===
if __name__ == "__main__":
    from config import PROGRAM_SHEETS_LIST
    driver = init_driver()

    try:
        for program, url in PROGRAM_URLS.items():
            sheet_name = PROGRAM_SHEETS_LIST.get(program)
            if sheet_name:
                process_program(program, url, sheet_name, driver)
            else:
                logging.warning(f"⚠️ Нет листа в таблице для программы: {program}")
    finally:
        driver.quit()