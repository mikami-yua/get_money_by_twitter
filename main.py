# main.py (v6 - 最终修正版，遵循API规则，只使用start_time)
import tweepy
import time
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

# 导入我们自己编写的模块
try:
    from . import config
    from .parser import extract_password
    from .notifier import send_red_packet_alert, send_system_alert
except ImportError:
    import config
    from parser import extract_password
    from notifier import send_red_packet_alert, send_system_alert

# --- 健康检测与状态管理的相关函数和配置 (保持不变) ---
STATE_FILE = Path("state.json")
MAX_CONSECUTIVE_FAILURES = 3


def load_last_tweet_id():  # 我们保留这个函数用于日志和未来分析
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            try:
                return json.load(f).get('last_processed_id')
            except:
                return None
    return None


def save_last_tweet_id(tweet_id: str):  # 保留保存函数
    with open(STATE_FILE, 'w') as f: json.dump({'last_processed_id': tweet_id}, f)


def get_next_active_account_index(accounts: list, current_index: int) -> int:
    num_accounts = len(accounts)
    if num_accounts == 0: return -1
    for i in range(1, num_accounts + 1):
        next_index = (current_index + i) % num_accounts
        if accounts[next_index].get('status', 'active') == 'active': return next_index
    return -1


def run_bot():
    print("▶️ 启动Twitter监控机器人 (v6 - start_time 最终版)...")

    accounts = config.ACCOUNTS
    for acc in accounts: acc['status'] = 'active'
    failure_counts = {acc['name']: 0 for acc in accounts}
    current_account_index = -1

    last_id = load_last_tweet_id()  # 加载ID，但仅供日志参考
    if last_id: print(f"ℹ️ 日志记录：上次处理到的推文ID为 {last_id}")

    while True:
        current_account_index = get_next_active_account_index(accounts, current_account_index)
        if current_account_index == -1: break

        account = accounts[current_account_index]
        client = None

        try:
            print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 切换到账户: {account['name']}")
            client = tweepy.Client(bearer_token=account['bearer_token'])

            # --- !! 核心修正：API调用中只保留 start_time !! ---
            now = datetime.now(timezone.utc)
            start_time_dt = now - timedelta(seconds=config.POLLING_INTERVAL_SECONDS)
            start_time_str = start_time_dt.isoformat()

            print(f"🔍 正在搜索 {start_time_str} 之后的新推文...")
            response = client.search_recent_tweets(
                query=config.SEARCH_QUERY,
                start_time=start_time_str,  # <-- 只使用这个参数来限定时间
                tweet_fields=["created_at"],
                max_results=10
            )

            # (请求成功，失败计数清零的逻辑不变)
            if failure_counts[account['name']] > 0:
                failure_counts[account['name']] = 0;
                print(f"✅ 账户 '{account['name']}' 已恢复...")

            if response.data:
                print(f"🎉 发现 {len(response.data)} 条新推文！")

                # (日志记录逻辑不变)
                with open("twitter.log", "a", encoding="utf-8") as log_file:
                    log_file.write(
                        f"\n===== BATCH at {datetime.now().isoformat()} | Account: {account['name']} =====\n")
                    for tweet in response.data: log_file.write(f"ID: {tweet.id}\n{tweet.text.replace('\n', ' ')}\n\n")

                # (更新ID的逻辑依然保留，用于我们自己调试和记录)
                newest_id_in_batch = response.meta.get('newest_id')
                if newest_id_in_batch:
                    save_last_tweet_id(newest_id_in_batch)
                    print(f"ℹ️ 日志记录：最新处理ID更新为 {newest_id_in_batch}")

                # (解析和通知逻辑不变)
                for tweet in reversed(response.data):
                    password = extract_password(tweet.text)
                    if password:
                        send_red_packet_alert(password, f"https://twitter.com/anyuser/status/{tweet.id}")
            else:
                print("💨 本轮没有发现新推文。")

        except Exception as e:
            # (错误处理和健康检测逻辑不变)
            print(f"⚠️ 账户 '{account['name']}' 发生错误: {e}")
            failure_counts[account['name']] += 1
            if failure_counts[account['name']] >= MAX_CONSECUTIVE_FAILURES:
                account['status'] = 'disabled';
                print(f"🚨 警报！账户 '{account['name']}' 已被禁用！")
                send_system_alert(f"账号失效警告：{account['name']}",
                                  f"账号 '{account['name']}' (Email: {account['emailid']}) 已被自动禁用，最后一次错误: {e}")

        print(f"\n😴 等待 {config.POLLING_INTERVAL_SECONDS} 秒...")
        time.sleep(config.POLLING_INTERVAL_SECONDS)

    print("\n\n🚨 所有可用账户均已失效，程序退出。")


if __name__ == "__main__":
    run_bot()