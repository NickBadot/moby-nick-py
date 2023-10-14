from selenium import webdriver
from selenium.webdriver.common.by import By
import time


def search_for_pictures_of_walruses():
    driver = webdriver.Chrome()   # driver stored locally, no need for path
    driver.get('http://www.google.com/');
    time.sleep(2)  # Let the user actually see something!
    search_box = driver.find_element(By.CSS_SELECTOR, '[name="q"]')
    search_box.send_keys('Pictures of Walruses')
    search_box.submit()
    time.sleep(3)
    driver.quit()


def test_title_contains(page, title):
    driver = webdriver.Chrome()
    driver.get(page)
    print("Print driver: %s" % driver)
    print("\nTitle is %s" % driver.title)
    assert title in driver.title


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
    search_for_pictures_of_walruses()
    test_title_contains('https://xkcd.com', 'Sign')


if __name__ == "__main__":
    main()