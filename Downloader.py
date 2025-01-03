import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, WebDriverException


# Function to read links from a file in the same directory as the script
def read_links_from_file(script_dir):
    file_path = os.path.join(script_dir, "links.txt")
    try:
        with open(file_path, "r") as file:
            links = file.read().splitlines()
        return links
    except FileNotFoundError:
        print(f"Error: File 'links.txt' not found in {script_dir}.")
        return []


# Function to wait for all downloads to complete
def wait_for_downloads(download_dir, timeout=300):
    """Wait for all downloads to finish by checking for .crdownload files."""
    start_time = time.time()
    while True:
        # Check for .crdownload files
        downloading_files = [f for f in os.listdir(download_dir) if f.endswith(".crdownload")]
        if not downloading_files:
            print("All downloads completed.")
            break
        # Timeout condition
        if time.time() - start_time > timeout:
            print("Timeout reached while waiting for downloads to complete.")
            break
        time.sleep(2)  # Check every 2 seconds


# Function to pause if active downloads exceed the limit
def pause_if_downloads_exceed_limit(download_dir, max_active_downloads):
    """Pause script if the number of active downloads exceeds the limit."""
    while True:
        active_downloads = [f for f in os.listdir(download_dir) if f.endswith(".crdownload")]
        if len(active_downloads) < max_active_downloads:
            break
        print(f"Active downloads: {len(active_downloads)}. Pausing until the number drops below {max_active_downloads}.")
        time.sleep(2)  # Check every 2 seconds


# Function to process each link
def process_links(links, download_dir, driver_path, max_active_downloads):
    # Ensure the download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Configure Chrome options for custom download directory
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": download_dir,  # Set custom download directory
        "download.prompt_for_download": False,       # Disable download prompt
        "safebrowsing.enabled": True                 # Enable safe browsing
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the WebDriver
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    for link in links:
        try:
            # Pause if downloads exceed the limit
            pause_if_downloads_exceed_limit(download_dir, max_active_downloads)

            # Open the link in the browser
            driver.get(link)
            time.sleep(5)  # Wait for the page to load

            while True:
                try:
                    # Locate and click the download button using its class
                    download_button = driver.find_element(By.CLASS_NAME, "link-button")
                    download_button.click()
                    time.sleep(5)  # Wait for the new tab to open
                except NoSuchElementException:
                    print(f"No download button found on {link}")
                    break

                # Switch to the newly opened tab
                window_handles = driver.window_handles
                if len(window_handles) > 1:
                    driver.switch_to.window(window_handles[-1])  # Switch to the latest tab
                    time.sleep(3)  # Wait for the tab to load

                    # Get the current URL of the new tab
                    current_url = driver.current_url
                    if current_url.startswith("https://fuckingfast"):
                        print(f"Valid site: {current_url}")
                        break  # Exit the retry loop if valid
                    else:
                        print(f"Invalid site: {current_url}. Closing new tab.")
                        driver.close()  # Close the new tab
                        driver.switch_to.window(window_handles[0])  # Switch back to the main tab
                else:
                    print("No new tab was opened.")
                    break  # Exit the retry loop if no tab opens

        except WebDriverException as e:
            print(f"Error processing {link}: {e}")

    # Wait for all downloads to complete
    wait_for_downloads(download_dir)

    # Close the browser
    driver.quit()


# Main program
if __name__ == "__main__":
    # Get the path to the script's directory
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Prompt user for the download directory
    download_directory = input("Enter the full path to the download directory: ").strip()

    # Get the path to ChromeDriver from the script's directory
    driver_path = os.path.join(script_dir, "chromedriver.exe")  # Assumes chromedriver.exe is in the same folder

    # Check if ChromeDriver exists
    if not os.path.exists(driver_path):
        print(f"Error: ChromeDriver not found at {driver_path}")
    else:
        # Prompt user for the maximum number of simultaneous downloads
        max_downloads = int(input("Enter the maximum number of simultaneous downloads: ").strip())

        # Read links from the links.txt file located in the same directory as the script
        fuckingfast_links = read_links_from_file(script_dir)

        # If links are found, process them
        if fuckingfast_links:
            process_links(fuckingfast_links, download_directory, driver_path, max_active_downloads=max_downloads)
        else:
            print("No links to process.")
