from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Initialize the WebDriver (assuming Chrome)
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")

driver = webdriver.Chrome(options=chrome_options)

# Open the webpage
url = "https://dashboard.internetcomputer.org/canister/tbsjh-jyaaa-aaaad-qg7nq-cai"
driver.get(url)

# Wait for the page to load
time.sleep(10)  # Adjust the sleep time as needed
