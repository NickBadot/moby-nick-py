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


def slogan_search_xkcd():
    # This method plays around with different ways to find the Slogan on the XKCD page using find_element
    # The slogan contains the word 'sarcasm' so we asset this string mathc to validate our result as well as
    # printing the HTML.

    driver = webdriver.Chrome()
    driver.get('https://xkcd.com')

    # Find the slogan by ID, it should have a unique ID
    slogan = driver.find_element(By.ID, 'slogan')
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    # here we use a CSS selector to find the slogan, selecting from a tag span with a value slogan
    slogan = driver.find_element(By.CSS_SELECTOR, "span#slogan")
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    # The next three checks are CSS selectors using string search on the ID value
    # By prefix using ^=
    slogan = driver.find_element(By.CSS_SELECTOR, "span[id^='slog']")
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    # By suffix  using $=
    slogan = driver.find_element(By.CSS_SELECTOR, "span[id$='ogan']")
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    # By substring using *=
    slogan = driver.find_element(By.CSS_SELECTOR, "span[id*='loga']")
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    # Here, we locate the slogan via relative XPATH - using absolute XPATH would look like:
    # /html/body/div[1]/div[2]/div[1]/span[2] and would break with any change to site structure
    slogan = driver.find_element(By.XPATH, '//*[@id="slogan"]')
    print(slogan.get_attribute("outerHTML"))
    assert "sarcasm" in slogan.text

    driver.quit()


def got_to_buttersafe_from_xkcd():
    driver = webdriver.Chrome()
    driver.get('https://xkcd.com')

    # Find the link via partial string match
    buttersafe_link = driver.find_element(By.PARTIAL_LINK_TEXT, 'Butter')
    time.sleep(2)
    buttersafe_link.click()
    time.sleep(2)
    driver.back()

    # Find the link via CSS selector, substring match
    buttersafe_link = driver.find_element(By.CSS_SELECTOR, "a[href*='uttersaf']")
    time.sleep(2)
    buttersafe_link.click()
    time.sleep(2)
    driver.back()

    driver.quit()


def main():
    slogan_search_xkcd()
    got_to_buttersafe_from_xkcd()


if __name__ == "__main__":
    main()