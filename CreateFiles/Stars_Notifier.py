from selenium import webdriver
from bs4 import BeautifulSoup
from win10toast import ToastNotifier
import time
import re
from tkinter import Tk, Label, Button, Entry, messagebox

URL = 'https://osrsportal.com/shooting-stars-tracker'

def hash_entry(location_value, world_value, tier_value):
    """Generate a hash based on the key details of a star."""
    return hash((location_value, world_value, tier_value))

def get_user_input():
    def on_submit():
        tier_value = entry.get()
        if tier_value.isdigit() and 1 <= int(tier_value) <= 9:
            window.user_input = int(tier_value)
            window.destroy()
        else:
            messagebox.showerror("Error", "Please enter a number between 1 and 9.")

    window = Tk()
    window.title("Minimum Tier of the Crashed Star")
    window.geometry("350x120")  # Increased size of window

    Label(window, text="Enter the minimum tier of star (1-9):").pack(pady=10)
    
    entry = Entry(window, width=25)  # entry width
    entry.pack(pady=5)
    
    submit_button = Button(window, text="Submit", command=on_submit, width=20, height=2)  
    submit_button.pack(pady=10)
    
    window.mainloop()
    
    return window.user_input


def make_entry_key(tier, location, world):
    return (tier, location, world)

def scrape_values(browser, min_tier):
    page_source = browser.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return None

    header = table.find_all('tr')[0]
    columns = [th.get_text() for th in header.find_all('th')]

    tier_index = columns.index('Tier')
    time_index = columns.index('Time')
    location_index = columns.index('Location')
    world_index = columns.index('World')

    def within_five_minutes(time_str):
        match = re.search(r'(\d+)m', time_str)
        if match:
            minutes = int(match.group(1))
            return minutes <= 5
        return False

    # Create a list of entries with relevant information, sort them by time, and then check for the desired tier.
    entries = []
    for row in table.find_all('tr')[1:]:
        cells = row.find_all('td')
        time_value = cells[time_index].get_text().strip()
        if within_five_minutes(time_value):
            tier_value = int(cells[tier_index].get_text().strip())
            if tier_value >= min_tier:
                location_value = cells[location_index].get_text().strip()
                world_value = cells[world_index].get_text().strip()
                entry = {
                    "time": time_value,
                    "location": location_value,
                    "world": world_value,
                    "tier": tier_value
                }
                entries.append(entry)

     # Sort entries by time such that the most recent one comes first
    entries.sort(key=lambda x: int(re.search(r'(\d+)m', x["time"]).group(1)))

    return entries



def send_notification(entry):
    toaster = ToastNotifier()
    tier = entry["tier"]
    message = f"Time: {entry['time']}, Location: {entry['location']}, World: {entry['world']}, Tier: {tier}"
    
    title = 'Scraped Data'
    if tier == 9:
        title = "TIER 9 - GO MINE IT NOW!"
    
    toaster.show_toast(title, message, duration=20)

if __name__ == "__main__":
    min_tier = get_user_input()
    
    browser = webdriver.Chrome()
    browser.get(URL)
    notified_entries = set()  # This set will store hashes of notified entries
    
    try:
        while True:
            valid_entries = scrape_values(browser, min_tier)

            for entry in valid_entries:
                entry_hash = hash_entry(entry["location"], entry["world"], entry["tier"])
                if entry_hash not in notified_entries:
                    print(f"Time: {entry['time']}, Location: {entry['location']}, World: {entry['world']}, Tier: {entry['tier']}")
                    send_notification(entry)
                    notified_entries.add(entry_hash)
                    time.sleep(10)
            time.sleep(10)
    except KeyboardInterrupt:
        print("Script terminated by user.")
    finally:
        browser.quit()