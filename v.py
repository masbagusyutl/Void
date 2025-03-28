import requests
import random
import time
import urllib.parse
import json
import os
from colorama import Fore, Style, init
import threading
import sys
import re

# Initialize colorama for colored output
init(autoreset=True)

def extract_username(initdata):
    """Extract username from URL-encoded initdata"""
    try:
        # Decode URL-encoded initdata
        decoded = urllib.parse.unquote(initdata)
        
        # Use regex to extract username
        match = re.search(r'"username":"([^"]*)"', decoded)
        if match:
            return match.group(1)
        return "Unknown"
    except Exception as e:
        print(Fore.RED + f"Gagal ekstrak username: {str(e)}")
        return "Unknown"

def print_welcome_message():
    print(Fore.WHITE + r"""
_  _ _   _ ____ ____ _    ____ _ ____ ___  ____ ____ ___ 
|\ |  \_/  |__| |__/ |    |__| | |__/ |  \ |__/ |  | |__]
| \|   |   |  | |  \ |    |  | | |  \ |__/ |  \ |__| |         
          """)
    print(Fore.GREEN + Style.BRIGHT + "Nyari Airdrop VOID")
    print(Fore.YELLOW + Style.BRIGHT + "Telegram: https://t.me/nyariairdrop")

def load_accounts():
    """Load accounts from data.txt"""
    try:
        with open('data.txt', 'r') as file:
            accounts = []
            for line in file:
                line = line.strip()
                if line:
                    # Automatically extract username if not explicitly provided
                    username = extract_username(line)
                    accounts.append((line, username))
            return accounts
    except FileNotFoundError:
        print(Fore.RED + "File data.txt tidak ditemukan!")
        return []

def load_proxies(filename='proxy.txt'):
    """Load proxies from a file"""
    try:
        with open(filename, 'r') as file:
            proxies = []
            for line in file:
                line = line.strip()
                if line:
                    parts = line.split(":")
                    if len(parts) == 4:
                        ip, port, user, password = parts
                        proxy_url = f"http://{user}:{password}@{ip}:{port}"
                    elif len(parts) == 2:
                        ip, port = parts
                        proxy_url = f"http://{ip}:{port}"
                    else:
                        continue
                    proxies.append(proxy_url)
        
        if proxies:
            print(Fore.BLUE + f"Berhasil memuat {len(proxies)} proxy.")
        return proxies
    except FileNotFoundError:
        print(Fore.YELLOW + f"File {filename} tidak ditemukan. Melanjutkan tanpa proxy.")
        return []

def get_proxy(proxies):
    """Retrieve a random proxy"""
    if not proxies:
        return None
    proxy_url = random.choice(proxies)
    return {"http": proxy_url, "https": proxy_url}

def authenticate_telegram(initdata, proxies=None):
    """Authenticate with Telegram using provided initdata"""
    try:
        url = "https://api.voidgame.io/api/auth/telegram"
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.voidgame.io",
            "Referer": "https://app.voidgame.io/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "Content-Length": "0",  # Sesuai dengan contoh data
            "initdata": initdata  # Kirim initdata sebagai header
        }

        proxy_config = get_proxy(proxies) if proxies else None

        response = requests.post(url, headers=headers, proxies=proxy_config)  # Tanpa payload
        response.raise_for_status()

        data = response.json()
        access_token = data['tokens']['access']

        print(Fore.GREEN + "Autentikasi berhasil!")
        return access_token
    except requests.exceptions.HTTPError as http_err:
        print(Fore.RED + f"Gagal autentikasi: {http_err.response.text}")  # Print detail error dari response
        return None
    except Exception as e:
        print(Fore.RED + f"Gagal autentikasi: {str(e)}")
        return None

def get_available_tasks(access_token, initdata, proxies=None):
    """Retrieve available tasks, excluding Telegram tasks and providing detailed task info"""
    try:
        url = "https://api.voidgame.io/api/tasks/my"
        headers = {
            "Authorization": access_token,
            "Accept": "*/*",
            "initdata": initdata
        }

        proxy_config = get_proxy(proxies) if proxies else None

        response = requests.get(url, headers=headers, proxies=proxy_config)
        response.raise_for_status()

        data = response.json()
        available_tasks = data.get('available', [])
        in_progress_tasks = data.get('inProgress', [])
        done_tasks = data.get('done', [])

        # Fungsi untuk mencetak detail tugas
        def print_task_details(tasks, status):
            if tasks:
                print(f"\n{status} Tugas:")
                for task in tasks:
                    print(f"- {task['title']}")
                    print(f"  Deskripsi: {task['description']}")
                    print(f"  Jenis: {task['type']}")
                    print(f"  Reward: {task['rewards'][0]['value']} koin")
                    print(f"  URL: {task.get('redirectUrl', 'Tidak ada URL')}")
                    
                    # Tambahkan instruksi manual untuk tugas TELEGRAM
                    if task['type'] == 'TELEGRAM':
                        print(Fore.RED + "  PERHATIAN: Tugas Telegram harus diselesaikan secara manual!")
                    
                    print()

        # Cetak detail tugas
        print_task_details(available_tasks, "Tersedia")
        print_task_details(in_progress_tasks, "Sedang Dikerjakan")
        print_task_details(done_tasks, "Selesai")

        # Filter out Telegram tasks from available tasks
        filtered_tasks = [
            task for task in available_tasks 
            if task['type'] != 'TELEGRAM'
        ]

        return filtered_tasks
    except requests.exceptions.HTTPError as http_err:
        print(Fore.RED + f"Gagal mendapatkan tugas: {http_err.response.text}")
        return []
    except Exception as e:
        print(Fore.RED + f"Gagal mendapatkan tugas: {str(e)}")
        return []

def start_task(access_token, task_id, task_title, initdata, proxies=None):
    """Start a specific task and potentially open its associated URL"""
    try:
        url = f"https://api.voidgame.io/api/tasks/start/{task_id}"
        headers = {
            "Authorization": access_token,
            "Accept": "*/*",
            "initdata": initdata
        }

        proxy_config = get_proxy(proxies) if proxies else None

        response = requests.post(url, headers=headers, proxies=proxy_config)
        response.raise_for_status()

        data = response.json()
        user_task_id = data.get("userTaskId")

        # Cetak detail tugas yang dimulai
        print(Fore.YELLOW + f"Memulai tugas: {task_title}")
        
        # Cek apakah tugas memiliki URL yang perlu dibuka
        if 'redirectUrl' in data and data['redirectUrl']:
            try:
                # Buka URL tugas di browser default
                import webbrowser
                print(Fore.BLUE + f"Membuka URL tugas: {data['redirectUrl']}")
                webbrowser.open(data['redirectUrl'])
                
                # Tambahkan jeda singkat setelah membuka URL
                time.sleep(3)
            except Exception as url_err:
                print(Fore.RED + f"Gagal membuka URL: {str(url_err)}")

        return {"userTaskId": user_task_id, "task_details": data}
    except requests.exceptions.HTTPError as http_err:
        print(Fore.RED + f"Gagal memulai tugas {task_title}: {http_err.response.text}")
        return None
    except Exception as e:
        print(Fore.RED + f"Gagal memulai tugas {task_title}: {str(e)}")
        return None

def complete_task(access_token, user_task_id, task_info, initdata, proxies=None):
    """Complete a specific task with detailed output"""
    try:
        url = f"https://api.voidgame.io/api/user-tasks/{user_task_id}/check"
        headers = {
            "Authorization": access_token,
            "Accept": "*/*",
            "initdata": initdata
        }

        proxy_config = get_proxy(proxies) if proxies else None

        response = requests.get(url, headers=headers, proxies=proxy_config)
        response.raise_for_status()

        # Parse the response
        result = response.json()
        
        # Cetak detail tugas yang diselesaikan
        print(Fore.GREEN + "Tugas Diselesaikan:")
        print(f"  Judul: {result['title']}")
        print(f"  Deskripsi: {result['description']}")
        print(f"  Jenis: {result['type']}")
        
        # Cetak reward
        if result['rewards']:
            reward = result['rewards'][0]
            print(f"  Reward: {reward['value']} {reward['type'].replace('_', ' ').lower()}")
        
        # Cetak URL terkait jika ada
        if result.get('redirectUrl'):
            print(f"  URL: {result['redirectUrl']}")
        
        # Cetak status akhir
        print(f"  Status: {result['status']}")

        return result
    except requests.exceptions.HTTPError as http_err:
        print(Fore.RED + f"Gagal menyelesaikan tugas: {http_err.response.text}")
        return None
    except Exception as e:
        print(Fore.RED + f"Gagal menyelesaikan tugas: {str(e)}")
        return None

def countdown_timer(duration):
    """Countdown timer with moving display"""
    for remaining in range(duration, 0, -1):
        sys.stdout.write(f"\r{Fore.CYAN}Waktu tersisa: {remaining} detik...")
        sys.stdout.flush()
        time.sleep(1)
    print("\n")

def process_account(account_data, proxies):
    """Process a single account"""
    try:
        initdata, username = account_data
        print(Fore.YELLOW + f"\n--- Memproses Akun: {username} ---")
        
        # Autentikasi
        access_token = authenticate_telegram(initdata, proxies)
        if not access_token:
            return False
        
        # Dapatkan tugas tersedia
        tasks = get_available_tasks(access_token, proxies)
        
        for task in tasks:
            # Mulai tugas
            started_task = start_task(access_token, task['id'], task['title'], proxies)
            if started_task:
                # Selesaikan tugas
                complete_task(access_token, started_task['userTaskId'], task['title'], proxies)
            
            # Jeda antar tugas
            time.sleep(2)
        
        return True
    except Exception as e:
        print(Fore.RED + f"Kesalahan saat memproses akun {username}: {str(e)}")
        return False

def main():
    """Main function to process user tasks and retrieve balances"""
    print_welcome_message()
    
    accounts = load_accounts()
    proxies = load_proxies()
    
    if not accounts:
        print(Fore.RED + "Tidak ada akun yang tersedia!")
        return
    
    print(Fore.BLUE + f"Total akun yang ditemukan: {len(accounts)}")
    
    for i, account in enumerate(accounts, 1):
        print(Fore.WHITE + f"\nMemproses Akun {i} dari {len(accounts)}")
        initdata, username = account
        
        # Autentikasi akun
        access_token = authenticate_telegram(initdata, proxies)
        if not access_token:
            print(Fore.RED + f"Gagal autentikasi untuk akun {username}, lewati akun ini.")
            continue
        
        # Ambil daftar tugas yang tersedia
        print(Fore.YELLOW + f"Mengambil tugas yang tersedia untuk akun {username}...")
        tasks = get_available_tasks(access_token, initdata, proxies)
        
        # Proses hanya tugas non-Telegram
        for task in tasks:
            # Pastikan tugas bukan bertipe TELEGRAM
            if task.get('type') != 'TELEGRAM':
                # Mulai tugas dan dapatkan userTaskId
                user_task_id = start_task(access_token, task['id'], task['title'], initdata, proxies)
                if user_task_id:
                    # Pastikan kita meneruskan seluruh informasi task
                    complete_task(access_token, user_task_id['userTaskId'], task, initdata, proxies)
                else:
                    print(Fore.RED + f"Gagal mendapatkan userTaskId untuk tugas: {task['title']}")
            time.sleep(2)  # Jeda antar tugas
        
        print(Fore.GREEN + f"Akun {username} selesai diproses!")
        time.sleep(5)  # Jeda antar akun
    
    print(Fore.CYAN + "\nSemua akun telah diproses!")

    # Hitung mundur 1 hari sebelum siklus berikutnya
    print(Fore.CYAN + "\nMenunggu 1 hari sebelum siklus berikutnya...")
    countdown_timer(24 * 60 * 60)  # 24 jam dalam detik

if __name__ == "__main__":
    main()
