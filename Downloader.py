import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    NoSuchWindowException
)


# Function to read links from a file
def read_links_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            links = file.read().splitlines()
        return links
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []


# Function to write the updated list of links back to the file
def update_links_file(file_path, updated_links):
    with open(file_path, "w") as file:
        file.write("\n".join(updated_links))
    print(f"Updated {file_path} with remaining links.")


# Function to check and remove already downloaded files
def remove_downloaded_links(links, download_dir):
    """Check if files corresponding to the links are already downloaded."""
    remaining_links = []
    for link in links:
        if "#" in link:
            file_name = link.split("#")[-1]
            file_path = os.path.join(download_dir, file_name)
            if os.path.exists(file_path):
                print(f"File already downloaded: {file_name}. Removing link from list.")
            else:
                remaining_links.append(link)
        else:
            print(f"Invalid link format (missing '#'): {link}. Skipping.")
            remaining_links.append(link)  # Keep invalid links in the list
    return remaining_links


# Function to wait for all downloads to complete
def wait_for_downloads(download_dir, timeout=300):
    """Wait for all downloads to finish by checking for .crdownload files."""
    start_time = time.time()
    while True:
        downloading_files = [f for f in os.listdir(download_dir) if f.endswith(".crdownload")]
        if not downloading_files:
            print("All downloads completed.")
            break
        if time.time() - start_time > timeout:
            print("Timeout reached while waiting for downloads to complete.")
            break
        time.sleep(2)


# Function to pause if active downloads exceed the limit
def pause_if_downloads_exceed_limit(download_dir, max_active_downloads):
    """Pause script if the number of active downloads exceeds the limit."""
    while True:
        active_downloads = [f for f in os.listdir(download_dir) if f.endswith(".crdownload")]
        if len(active_downloads) < max_active_downloads:
            break
        print(f"Active downloads: {len(active_downloads)}. Pausing until the number drops below {max_active_downloads}.")
        time.sleep(2)


# Function to safely switch to a window
def safe_switch_to_window(driver, window_handle):
    try:
        driver.switch_to.window(window_handle)
    except NoSuchWindowException:
        print(f"Window {window_handle} no longer exists.")


# Function to process each link
def process_links(links, download_dir, driver_path, max_active_downloads, file_path):
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
    driver = None  # Initialize driver as None

    while links:
        try:
            # Update the list before opening ChromeDriver
            print("Updating links before opening ChromeDriver...")
            links = remove_downloaded_links(links, download_dir)
            update_links_file(file_path, links)

            if not links:
                print("All files downloaded. Exiting...")
                break

            print("Opening ChromeDriver...")
            driver = webdriver.Chrome(service=service, options=chrome_options)

            for link in links[:]:  # Iterate over a copy of the list
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
                            safe_switch_to_window(driver, window_handles[-1])  # Switch to the latest tab
                            time.sleep(3)  # Wait for the tab to load

                            # Get the current URL of the new tab
                            current_url = driver.current_url
                            if current_url.startswith("https://fuckingfast"):
                                print(f"Valid site: {current_url}")
                                links.remove(link)  # Remove the link after successful processing
                                break  # Exit the retry loop if valid
                            else:
                                print(f"Invalid site: {current_url}. Closing new tab.")
                                driver.close()  # Close the new tab
                                safe_switch_to_window(driver, window_handles[0])  # Switch back to the main tab
                        else:
                            print("No new tab was opened.")
                            break  # Exit the retry loop if no tab opens

                except WebDriverException as e:
                    print(f"Error processing {link}: {e}")
                    break  # Break the loop to restart ChromeDriver and handle errors

        except Exception as e:
            print(f"Unexpected error: {e}")

        finally:
            # Wait for all downloads to complete
            wait_for_downloads(download_dir)

            # Close the browser if it's open
            if driver:
                driver.quit()
                driver = None  # Set driver to None to reopen it on restart

            # Update links.txt with the remaining links
            print("Updating links.txt with remaining links...")
            links = remove_downloaded_links(links, download_dir)
            update_links_file(file_path, links)

            # Check if there are remaining links
            if not links:
                print("All downloads completed successfully.")
                break


# Main program
if __name__ == "__main__":
    # Get the path to the script's directory
    script_dir = os.path.dirname(os.path.realpath(__file__))

    # Prompt user for the links file
    links_file = input("Enter the name of the links file (e.g., links.txt): ").strip()
    links_file_path = os.path.join(script_dir, links_file)

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

        # Read links from the links file
        game_links = read_links_from_file(links_file_path)

        if game_links:
            process_links(game_links, download_directory, driver_path, max_active_downloads=max_downloads, file_path=links_file_path)
        else:
            print(f"No links to process in {links_file_path}.")
