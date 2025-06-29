# twitter_bot/main.py
import tweepy
import time
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

# 从同级目录的 config.py 文件中导入我们的配置
try:
    from . import config
    from .parser import extract_password
    from .notifier import send_red_packet_alert, send_system_alert
except ImportError:
    import config
    from parser import extract_password
    from notifier import send_red_packet_alert, send_system_alert


STATE_FILE = Path("state.json")
# --- 新增的健康检测配置 ---
MAX_CONSECUTIVE_FAILURES = 3

MAX_SAVED_IDS = 10  # 新增配置：最多保存10个历史ID


def load_last_tweet_id() -> str | None:
    """从state.json加载ID列表，并返回最新的一个ID"""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            try:
                state = json.load(f)
                # state['processed_ids'] 是一个列表，最新的在最后
                if state.get('processed_ids'):
                    return state['processed_ids'][-1]
            except (json.JSONDecodeError, KeyError):
                return None
    return None


def save_last_tweet_id(tweet_id: str):
    """将新的ID加入列表，并维护列表大小不超过MAX_SAVED_IDS"""
    history_ids = []
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            try:
                state = json.load(f)
                if isinstance(state.get('processed_ids'), list):
                    history_ids = state['processed_ids']
            except (json.JSONDecodeError, KeyError):
                pass

    # 将新的ID追加到列表末尾
    history_ids.append(tweet_id)

    # 如果列表超长，就从前面删除旧的ID
    while len(history_ids) > MAX_SAVED_IDS:
        history_ids.pop(0)

    # 将更新后的列表写回文件
    with open(STATE_FILE, 'w') as f:
        json.dump({'processed_ids': history_ids}, f)

def get_next_active_account_index(accounts: list, current_index: int) -> int:
    """从当前索引的下一个开始，寻找并返回活动账户的索引"""
    num_accounts = len(accounts)
    if num_accounts == 0:
        return -1

    for i in range(1, num_accounts + 1):
        next_index = (current_index + i) % num_accounts
        if accounts[next_index].get('status', 'active') == 'active':
            return next_index
    return -1  # 返回-1表示没有可用的活动账户了


def run_bot():
    """
    程序主函数 (最终版)
    集成了多账户轮换、健康检测、精准去重、ID历史记录和推文日志功能。
    """
    print("▶️ 启动Twitter监控机器人...")

    # --- 1. 初始化账户状态和失败计数器 ---
    accounts = config.ACCOUNTS
    for acc in accounts:
        acc['status'] = 'active'

    failure_counts = {acc['name']: 0 for acc in accounts}
    current_account_index = -1

    # --- 2. 加载最新的“书签”ID ---
    last_id = load_last_tweet_id()
    if last_id:
        print(f"ℹ️ 已加载上次处理到的推文ID (书签): {last_id}")
    else:
        print("ℹ️ 未发现历史状态，将从最新的推文开始搜索。")

    # --- 3. 进入主循环 ---
    while True:
        current_account_index = get_next_active_account_index(accounts, current_account_index)

        if current_account_index == -1:
            print("\n🚨 所有账户均已失效！程序将在1小时后退出以待修复。")
            time.sleep(3600)
            break

        account = accounts[current_account_index]
        client = None

        try:
            # --- 3a. 初始化客户端 ---
            print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 切换到账户: {account['name']}")
            client = tweepy.Client(bearer_token=account['bearer_token'])

            # --- 3b. 发起API请求 ---
            # 同时使用 start_time 和 since_id 来实现最高效的精准去重
            now = datetime.now(timezone.utc)
            start_time_dt = now - timedelta(days=1)
            start_time_str = start_time_dt.isoformat()

            print(f"🔍 正在搜索 (书签ID: {last_id})...")
            response = client.search_recent_tweets(
                query=config.SEARCH_QUERY,
                since_id=last_id,
                start_time=start_time_str,
                tweet_fields=["created_at"],
                max_results=10
            )

            # --- 请求成功，重置该账户的失败计数器 ---
            if failure_counts[account['name']] > 0:
                failure_counts[account['name']] = 0
                print(f"✅ 账户 '{account['name']}' 已恢复，失败计数清零。")

            # --- 3c. 处理返回结果 ---
            if response.data:
                print(f"🎉 发现 {len(response.data)} 条新推文！")

                # --- !! 新功能：将所有下载的推文写入日志 !! ---
                try:
                    with open("twitter.log", "a", encoding="utf-8") as log_file:
                        log_file.write(
                            f"\n===== BATCH at {datetime.now().isoformat()} | Account: {account['name']} =====\n")
                        for tweet in response.data:
                            log_file.write(f"ID: {tweet.id} | Created at: {tweet.created_at}\n")
                            log_file.write(tweet.text.replace('\n', ' ') + '\n')
                            log_file.write("-" * 20 + "\n")
                    print("✍️  已将获取到的推文追加到 twitter.log 文件。")
                except Exception as log_e:
                    print(f"❌ 写入日志文件失败: {log_e}")
                # --- 日志记录结束 ---

                # --- 3d. 更新“书签”ID ---
                newest_id_in_batch = response.meta.get('newest_id')
                if newest_id_in_batch:
                    last_id = newest_id_in_batch
                    save_last_tweet_id(last_id)
                    print(f"ℹ️ 书签已更新为: {last_id}")

                # --- 3e. 遍历推文进行解析和通知 ---
                for tweet in reversed(response.data):
                    print(f"\n--- 正在处理推文ID: {tweet.id} ---")
                    password = extract_password(tweet.text)
                    if password:
                        tweet_url = f"https://twitter.com/anyuser/status/{tweet.id}"
                        send_red_packet_alert(password, tweet_url)
            else:
                print("💨 本轮没有发现新推文。")

        except Exception as e:
            # --- 3f. 错误处理与健康检测 ---
            print(f"⚠️ 账户 '{account['name']}' 发生未知错误: {e}")
            failure_counts[account['name']] += 1
            print(f"    -> 连续失败次数: {failure_counts[account['name']]}/{MAX_CONSECUTIVE_FAILURES}")

            if failure_counts[account['name']] >= MAX_CONSECUTIVE_FAILURES:
                account['status'] = 'disabled'
                print(f"🚨 警报！账户 '{account['name']}' 已被禁用！")
                alert_subject = f"账号失效警告：{account['name']}"
                alert_body = f"账号 '{account['name']}' (Email: {account['emailid']}) 已被自动禁用，最后一次错误: {e}"
                send_system_alert(alert_subject, alert_body)

        # --- 3g. 等待下一个轮询周期 ---
        print(f"\n😴 等待 {config.POLLING_INTERVAL_SECONDS} 秒...")
        time.sleep(config.POLLING_INTERVAL_SECONDS)

    print("\n\n🚨 所有账户均已失效或没有可用账户，程序退出。")

if __name__ == "__main__":
    run_bot()