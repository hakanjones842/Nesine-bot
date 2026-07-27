# Nesine-botimport time
import requests
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By

BOT_TOKEN = "8996832177:AAErDRfGeCCUkyEtSEYFn5wIym88Uieul3g"
CHAT_ID = "8671080510"
CACHE_FILE = "odds_cache.json"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=8)
    except Exception as e:
        print(f"Telegram Hatası: {e}")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    previous_odds_cache = load_cache()
    detected_current_run = {}

    try:
        print("🌐 Nesine bülteni taranıyor (Bulut Modu)...")
        driver.get("https://www.nesine.com/iddaa")
        time.sleep(12)
        
        tabs_count = 0
        try:
            tabs = driver.find_elements(By.XPATH, "//div[contains(@class, 'date')]//button | //div[contains(@class, 'day')]//div | //ul[contains(@class, 'date')]//li | //a[contains(@class, 'date')]")
            tabs_count = len(tabs)
        except:
            pass
            
        iterations = max(1, tabs_count)
        
        for idx in range(iterations):
            try:
                if tabs_count > 0:
                    current_tabs = driver.find_elements(By.XPATH, "//div[contains(@class, 'date')]//button | //div[contains(@class, 'day')]//div | //ul[contains(@class, 'date')]//li | //a[contains(@class, 'date')]")
                    if idx < len(current_tabs):
                        current_tabs[idx].click()
                        time.sleep(4)
            except:
                pass
                
            body_text = driver.execute_script("return document.body.innerText;")
            lines = body_text.split('\n')
            cleaned_lines = [l.strip() for l in lines if l.strip()]
            
            i = 0
            while i < len(cleaned_lines):
                line = cleaned_lines[i]
                if " - " in line and len(line) < 50 and not any(w in line for w in ["Giriş", "Üye", "Bülten", "Canlı"]):
                    is_live = False
                    for prev_idx in range(max(0, i - 6), min(len(cleaned_lines), i + 3)):
                        if "canli" in cleaned_lines[prev_idx].lower():
                            is_live = True
                            break
                    if is_live:
                        i += 1
                        continue
                    
                    current_match = line
                    odds_found = []
                    for j in range(i + 1, min(i + 15, len(cleaned_lines))):
                        next_line = cleaned_lines[j]
                        if "," in next_line or "." in next_line:
                            val_str = next_line.replace(",", ".")
                            try:
                                val = float(val_str)
                                if 1.01 <= val <= 25.0:
                                    odds_found.append(val)
                            except ValueError:
                                pass
                    
                    if len(odds_found) >= 5:
                        detected_current_run[current_match] = {"Alt": odds_found[3], "Üst": odds_found[4]}
                i += 1

        print(f"📊 Toplam Taranan Maç: {len(detected_current_run)}")
        
        drop_alerts = []
        for match, odds in detected_current_run.items():
            alt_curr = odds["Alt"]
            ust_curr = odds["Üst"]
            
            if match in previous_odds_cache:
                alt_prev = previous_odds_cache[match]["Alt"]
                ust_prev = previous_odds_cache[match]["Üst"]
                
                drops = []
                if alt_curr < alt_prev:
                    drops.append(f"📉 2.5 Alt Düştü: {alt_prev} ➡️ {alt_curr}")
                if ust_curr < ust_prev:
                    drops.append(f"📉 2.5 Üst Düştü: {ust_prev} ➡️ {ust_curr}")
                    
                if drops:
                    alert_text = f"⚽ *{match}*\n" + "\n".join(drops)
                    drop_alerts.append(alert_text)
            
        save_cache(detected_current_run)
        
        if drop_alerts:
            final_msg = "🚨 *ORANI DÜŞEN MAÇLAR (2.5 Alt/Üst)*\n\n" + "\n\n".join(drop_alerts)
            send_telegram_alert(final_msg)
            print("📲 Oran düşüşü Telegram'a iletildi!")
        else:
            print("ℹ️ Düşüş tespit edilmedi.")
            
    except Exception as err:
        print(f"❌ Hata: {err}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
