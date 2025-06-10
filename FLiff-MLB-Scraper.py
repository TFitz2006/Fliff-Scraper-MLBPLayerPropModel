import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TARGET_PROPS = [
    "PITCHER STRIKEOUTS", "PITCHER OUTS RECORDED", "PITCHER WALKS",
    "PITCHER HITS ALLOWED", "PITCHER EARNED RUNS", "BATTER HITS",
    "BATTER HOME RUNS", "BATTER RBIS", "BATTER RUNS", "BATTER WALKS",
    "BATTER HITS AND RUNS AND RBIS", "BATTER SINGLES", "BATTER STOLEN BASES",
    "BATTER STRIKEOUTS"
]

class Player:
    def __init__(self, name):
        self.name = name
        self.props = {prop: {"over": None, "under": None} for prop in TARGET_PROPS}

    def set_prop(self, category, bets):
        if len(bets) >= 2:
            over_label = bets[0]["label"]
            under_label = bets[1]["label"]
            over_line = over_label.split()[-1]
            under_line = under_label.split()[-1]
            self.props[category] = {
                "over": [over_line, bets[0]["odds"]],
                "under": [under_line, bets[1]["odds"]]
            }

    def to_dict(self):
        return {self.name: self.props}

def setup_driver():
    mobile_emulation = {
        "deviceMetrics": {"width": 390, "height": 844},
        "userAgent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/14.0 Mobile/15E148 Safari/604.1"
        )
    }
    options = Options()
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    return webdriver.Chrome(service=Service("/opt/homebrew/bin/chromedriver"), options=options)

def collect_games(driver):
    driver.get("https://sports.getfliff.com/sports?channelId=441")
    wait = WebDriverWait(driver, 6)
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card-info-container.double-grid-card.card-info-container--no-border")))
    blocks = driver.find_elements(By.CSS_SELECTOR, "div.card-info-container.double-grid-card.card-info-container--no-border")

    games = []
    for block in blocks:
        if block.find_elements(By.CLASS_NAME, "live-indicator"):
            continue
        teams = block.find_elements(By.CLASS_NAME, "card-row-header__team")
        if len(teams) == 2:
            label = f"{teams[0].text.strip()} vs {teams[1].text.strip()}"
            games.append({"label": label, "block": block})
    return games

def open_game(driver, label):
    blocks = driver.find_elements(By.CSS_SELECTOR, "div.card-info-container.double-grid-card.card-info-container--no-border")
    for block in blocks:
        teams = block.find_elements(By.CLASS_NAME, "card-row-header__team")
        if len(teams) == 2 and f"{teams[0].text.strip()} vs {teams[1].text.strip()}" == label:
            driver.execute_script("arguments[0].scrollIntoView(true);", teams[0])
            driver.execute_script("arguments[0].click();", teams[0])
            time.sleep(0.6)
            return True
    return False

def scrape_props(driver):
    players = {}
    headers = driver.find_elements(By.CLASS_NAME, "market-title__text")
    for header in headers:
        category = header.text.strip().upper()
        if category not in TARGET_PROPS:
            continue
        try:
            container = header.find_element(By.XPATH, "./ancestor::div[contains(@class, 'market-title')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", container)
            driver.execute_script("arguments[0].click();", container)
            try:
                show_all = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Show All']/ancestor::button"))
                )
                driver.execute_script("arguments[0].click();", show_all)
                time.sleep(0.2)
            except:
                pass
            props = driver.find_elements(By.CSS_SELECTOR, "div.more-markets-item-option-multiple")
            for block in props:
                player_name = block.find_element(By.CLASS_NAME, "more-markets-item-option-multiple__text").text.strip()
                bets = []
                for bet in block.find_elements(By.CLASS_NAME, "more-markets-item-option"):
                    try:
                        label = bet.find_element(By.CLASS_NAME, "card-cell-param-label").text.strip()
                        odds = bet.find_element(By.CLASS_NAME, "card-cell-label").text.strip()
                        bets.append({"label": label, "odds": odds})
                    except:
                        continue
                over = next((b for b in bets if "Over" in b["label"]), None)
                under = next((b for b in bets if "Under" in b["label"]), None)
                if over and under:
                    if player_name not in players:
                        players[player_name] = Player(player_name)
                    players[player_name].set_prop(category, [over, under])
        except:
            continue
    return players

def main():
    driver = setup_driver()
    all_games_output = []

    try:
        print("\n Loading MLB game list...")
        games = collect_games(driver)

        if not games:
            print(" No MLB games found.")
            return

        for i, game in enumerate(games):
            print(f"[{i}] {game['label']}")

        selection = input("\nEnter game numbers separated by commas: ")
        selected = [games[int(i.strip())] for i in selection.split(",") if i.strip().isdigit()]

        for game in selected:
            print(f"\n▶️ Scraping: {game['label']}")
            if not open_game(driver, game["label"]):
                print(f"⚠️ Could not click {game['label']}")
                continue

            try:
                WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'tab-filter') and text()='Player Props']"))
                ).click()
            except:
                print("⚠️ Could not open Player Props tab.")
                continue

            player_data = scrape_props(driver)

            all_games_output.append({
                "matchup": game["label"],
                "props": {name: p.to_dict()[name] for name, p in player_data.items()}
            })

            try:
                back = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.header-button--solid"))
                )
                driver.execute_script("arguments[0].click();", back)
                time.sleep(1)
            except:
                print("⚠️ Could not go back.")
                break

    finally:
        driver.quit()

    with open("mlb_props_output.json", "w") as f:
        json.dump({"games": all_games_output}, f, indent=2)
    print("\n Saved to mlb_props_output.json")

if __name__ == "__main__":
    main()
