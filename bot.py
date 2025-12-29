import requests
import time
import json
from datetime import datetime

# ============= CONFIGURATION =============
# Fill these in with your actual tokens
TELEGRAM_BOT_TOKEN = "8558259876:AAEpbIfsrC8xB4TrHeJeNlNQdb6xNSd_eyE"  # Get from @BotFather
TELEGRAM_CHAT_ID = "7338254131"  # Get from @userinfobot
TWITTER_BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAGJA6gEAAAAA12nOBlMhgKbb73Yoj15b3VBMV4w%3D3YwsqvgLULvKMo5IiTirhhbexO7PnTU8DM1XxMZqrd6XhavM7S"  # Get from developer.twitter.com

# Follower range
MIN_FOLLOWERS = 30
MAX_FOLLOWERS = 5000

# Categories to monitor
CATEGORIES = {
    'DeFi': ['defi', 'decentralized finance', 'dex', 'swap', 'liquidity'],
    'NFT': ['nft', 'non-fungible', 'collectible', 'pfp', 'mint'],
    'GameFi': ['gamefi', 'play to earn', 'p2e', 'gaming', 'metaverse'],
    'AI': ['ai crypto', 'artificial intelligence', 'machine learning', 'ai agent'],
    'Yield Farming': ['yield farming', 'yield', 'farm', 'apr', 'apy'],
    'Staking': ['staking', 'stake', 'validator', 'staking rewards'],
    'Lending': ['lending', 'lend', 'credit protocol', 'borrow'],
    'Borrowing': ['borrowing', 'loan', 'collateral', 'cdp'],
    'Memecoin': ['memecoin', 'meme coin', 'meme token', 'community token', 'fair launch']
}

# Search queries to monitor
SEARCH_QUERIES = [
    'launching new defi protocol',
    'new nft project',
    'gamefi launch',
    'ai crypto project',
    'yield farming protocol',
    'new staking platform',
    'lending protocol launch',
    'web3 project launching',
    'new token launch',
    'presale launching',
    'new memecoin',
    'meme coin launch',
    'fair launch token'
]

# Track already notified projects to avoid duplicates
notified_projects = set()

# ============= FUNCTIONS =============

def send_telegram_message(message):
    """Send alert to Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("✅ Telegram alert sent successfully")
        else:
            print(f"❌ Telegram error: {response.text}")
    except Exception as e:
        print(f"❌ Error sending Telegram: {e}")


def detect_category(text):
    """Detect which category a project belongs to"""
    text_lower = text.lower()
    detected_categories = []
    
    for category, keywords in CATEGORIES.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_categories.append(category)
    
    return detected_categories if detected_categories else ['Other']


def search_twitter(query):
    """Search Twitter for recent tweets matching query"""
    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
    }
    params = {
        "query": f"{query} -is:retweet lang:en",
        "max_results": 10,
        "tweet.fields": "created_at,public_metrics,author_id",
        "expansions": "author_id",
        "user.fields": "username,public_metrics,description"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            print("⚠️ Rate limit hit, waiting...")
            time.sleep(60)
            return None
        else:
            print(f"❌ Twitter API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error searching Twitter: {e}")
        return None


def process_results(data):
    """Process Twitter results and send alerts for qualifying projects"""
    if not data or 'data' not in data:
        return 0
    
    tweets = data.get('data', [])
    users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
    
    found_count = 0
    
    for tweet in tweets:
        author_id = tweet.get('author_id')
        user = users.get(author_id)
        
        if not user:
            continue
        
        username = user.get('username')
        followers = user.get('public_metrics', {}).get('followers_count', 0)
        
        # Check follower range
        if MIN_FOLLOWERS <= followers <= MAX_FOLLOWERS:
            # Check if we already notified about this project
            if username in notified_projects:
                continue
            
            # Detect categories
            tweet_text = tweet.get('text', '')
            user_description = user.get('description', '')
            combined_text = f"{tweet_text} {user_description}"
            categories = detect_category(combined_text)
            
            # Create Telegram message
            message = f"""
🚨 *New Web3 Project Detected!*

📱 *Project:* @{username}
👥 *Followers:* {followers:,}
🏷️ *Categories:* {', '.join(categories)}

📝 *Tweet:*
{tweet_text[:280]}

🔗 [View Profile](https://twitter.com/{username})
🐦 [View Tweet](https://twitter.com/{username}/status/{tweet['id']})

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            # Send alert
            send_telegram_message(message)
            notified_projects.add(username)
            found_count += 1
            
            # Small delay to avoid spamming
            time.sleep(2)
    
    return found_count


def scan_twitter():
    """Main scanning function"""
    print(f"\n{'='*60}")
    print(f"🔍 Starting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    total_scanned = 0
    total_found = 0
    
    for i, query in enumerate(SEARCH_QUERIES, 1):
        print(f"\n[{i}/{len(SEARCH_QUERIES)}] Searching: '{query}'")
        
        results = search_twitter(query)
        if results:
            found = process_results(results)
            tweets_count = len(results.get('data', []))
            total_scanned += tweets_count
            total_found += found
            
            print(f"   ✓ Scanned {tweets_count} tweets, found {found} new projects")
        
        # Rate limit protection - wait between queries
        time.sleep(10)
    
    print(f"\n{'='*60}")
    print(f"📊 Scan Complete!")
    print(f"   Total tweets scanned: {total_scanned}")
    print(f"   New projects found: {total_found}")
    print(f"   Total tracked projects: {len(notified_projects)}")
    print(f"{'='*60}\n")


def main():
    """Main loop - runs every 24 hours"""
    print("🤖 Web3 Early Project Detector Bot Started!")
    print(f"📡 Monitoring follower range: {MIN_FOLLOWERS:,} - {MAX_FOLLOWERS:,}")
    print(f"🔄 Scanning every 24 hours (daily)")
    print(f"📱 Sending alerts to Telegram Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"🏷️ Categories: {', '.join(CATEGORIES.keys())}")
    
    # Check if tokens are configured
    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("\n⚠️ WARNING: Please configure your tokens in the script first!")
        print("   1. TELEGRAM_BOT_TOKEN")
        print("   2. TELEGRAM_CHAT_ID")
        print("   3. TWITTER_BEARER_TOKEN")
        return
    
    # Send startup notification
    send_telegram_message("🤖 *Web3 Project Detector Bot Started!*\n\nMonitoring for new projects...")
    
    # Main loop
    while True:
        try:
            scan_twitter()
            
            # Wait 24 hours before next scan
            print(f"⏳ Waiting 24 hours until next scan...")
            print(f"   Next scan at: {datetime.fromtimestamp(time.time() + 86400).strftime('%Y-%m-%d %H:%M:%S')}\n")
            time.sleep(86400)  # 86400 seconds = 24 hours
            
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            send_telegram_message("🛑 *Bot Stopped*\n\nWeb3 Project Detector has been shut down.")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    main()