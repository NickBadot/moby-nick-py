from selenium import webdriver
from selenium.webdriver.common.by import By
import time


def verify_driver_works():
    driver = webdriver.Chrome()   # driver stored locally, no need for path
    driver.get('http://www.google.com/');
    time.sleep(2)  # Let the user actually see something!
    search_box = driver.find_element(By.CSS_SELECTOR, '[name="q"]')
    search_box.send_keys('Hello  Selenium')
    search_box.submit()
    time.sleep(3)
    driver.quit()


def list_elements_by_page_and_tag(page, tag):
    driver = webdriver.Chrome()
    driver.get(page)
    time.sleep(2)
    elements = driver.find_elements(By.TAG_NAME, tag)
    i = 0
    for element in elements:
        print("Element %s is %s\n" % (i, element))
        i += 1
    time.sleep(3)
    driver.quit()


def main():
    verify_driver_works()
    list_elements_by_page_and_tag('https://xkcd.com', 'div')


if __name__ == "__main__":
    main()