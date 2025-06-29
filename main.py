# twitter_bot/main.py
import tweepy
import time
from datetime import datetime, timezone, timedelta

# 从同级目录的 config.py 文件中导入我们的配置
try:
    from . import config
    from .parser import extract_password
    from .notifier import send_red_packet_alert, send_system_alert
except ImportError:
    import config
    from parser import extract_password
    from notifier import send_red_packet_alert, send_system_alert

# --- 新增的健康检测配置 ---
MAX_CONSECUTIVE_FAILURES = 3


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

def run_bot1():
    """程序主函数，使用 start_time 机制进行高精度、时效性过滤"""
    print("▶️ 启动Twitter监控机器人 (start_time 极限过滤模式)...")

    # 我们使用单账户配置
    account = config.ACCOUNTS[4]
    client = tweepy.Client(
        bearer_token=account['bearer_token'],
        consumer_key=account['api_key'],
        consumer_secret=account['api_secret'],
        access_token=account['access_token'],
        access_token_secret=account['access_token_secret'],
        wait_on_rate_limit=True
    )
    print(f"✅ 客户端初始化成功，使用账户: {account['name']}")

    while True:
        try:
            # --- 核心改动：动态计算 start_time ---
            # 获取当前的UTC时间
            now = datetime.now(timezone.utc)
            # 计算起始时间（例如：20分钟前）
            # 我们稍微多减一点时间（比如+5秒），作为网络延迟等的缓冲
            start_time_dt = now - timedelta(seconds=config.POLLING_INTERVAL_SECONDS + 5)
            # 将时间格式化为 Twitter API 要求的 RFC 3339 格式
            start_time_str = start_time_dt.isoformat()

            print(f"\n🔍 正在搜索 {start_time_str} 之后的新推文...")

            response = client.search_recent_tweets(
                query=config.SEARCH_QUERY,
                start_time=start_time_str,  # 使用 start_time 参数
                tweet_fields=["created_at"],
                max_results=10
            )

            # --- 后续处理逻辑不变 ---
            if response.data:
                print(f"🎉 发现 {len(response.data)} 条通过[服务器端]过滤的推文！")

                # Twitter 默认返回的是从新到旧，为了逻辑清晰，我们反转一下
                # Twitter默认返回结果是从新到旧，我们反转它，按时间顺序处理
                for tweet in reversed(response.data):
                    print(f"\n--- 处理推文ID: {tweet.id} | 发布于: {tweet.created_at} ---")

                    # --- 2d. 调用解析器 ---
                    password = extract_password(tweet.text)  # 此函数来自 parser.py

                    if password:
                        # 如果解析器返回了结果（不是None）
                        print(f"💰 成功提取到口令: {password}")
                        tweet_url = f"https://twitter.com/anyuser/status/{tweet.id}"

                        # --- 2e. 调用通知器 ---
                        print("🚀 发现目标！正在调用邮件通知...")
                        send_email_alert(password, tweet_url)  # 此函数来自 notifier.py
                    # 如果password是None，解析器的日志已经打印了“未匹配”，这里无需额外打印

            else:
                print("💨 本轮没有发现符合所有过滤条件的推文。")

        except Exception as e:
            print(f"❌ 发生错误: {e}")

        print(f"\n😴 等待 {config.POLLING_INTERVAL_SECONDS} 秒后进行下一轮搜索...")
        time.sleep(config.POLLING_INTERVAL_SECONDS)


def run_bot():
    print("▶️ 启动Twitter监控机器人 (5账号高速轮换模式)...")

    accounts = config.ACCOUNTS
    if len(accounts) < 5:
        print(f"⚠️ 警告：当前配置了 {len(accounts)} 个账户，不足5个。可能无法达到3分钟的更新频率。")

    for acc in accounts:
        acc['status'] = 'active'

    failure_counts = {acc['name']: 0 for acc in accounts}
    current_account_index = -1  # 确保从第一个账户开始

    # --- 主循环 ---
    while True:
        # --- 1. 获取下一个健康的账户 ---
        current_account_index = get_next_active_account_index(accounts, current_account_index)

        if current_account_index == -1:
            print("\n🚨 所有账户均已失效！程序将在1小时后退出以待修复。")
            time.sleep(3600)
            break

        account = accounts[current_account_index]
        client = None

        try:
            # --- 2. 初始化客户端并请求 ---
            print(f"\n🔄 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 切换到账户: {account['name']}")
            client = tweepy.Client(bearer_token=account['bearer_token'])  # 不再自动等待速率限制

            now = datetime.now(timezone.utc)
            # 时间窗口应该是“账号数 * 轮询间隔”，确保不漏数据
            time_window = len(accounts) * config.POLLING_INTERVAL_SECONDS
            start_time_dt = now - timedelta(seconds=time_window)
            start_time_str = start_time_dt.isoformat()

            print(f"🔍 正在搜索...")
            response = client.search_recent_tweets(
                query=config.SEARCH_QUERY, start_time=start_time_str,
                tweet_fields=["created_at"], max_results=10
            )

            # --- 请求成功，重置失败计数 ---
            if failure_counts[account['name']] > 0:
                print(f"✅ 账户 '{account['name']}' 已恢复，失败计数清零。")
                failure_counts[account['name']] = 0

            # --- 3. 处理结果 ---
            if response.data:
                print(f"🎉 发现 {len(response.data)} 条符合条件的推文！")
                for tweet in reversed(response.data):
                    password = extract_password(tweet.text)
                    if password:
                        tweet_url = f"https://twitter.com/anyuser/status/{tweet.id}"
                        send_red_packet_alert(password, tweet_url)
            else:
                print("💨 本轮没有发现符合条件的推文。")

        except tweepy.errors.TooManyRequests:
            # --- 4a. 如果是速率超限，这是“正常”的，直接进入休眠，等待下一个账号 ---
            print(f"⌛️ 账户 '{account['name']}' 本轮请求机会已用完（正常现象），等待轮换。")
            # 请求成功，重置失败计数
            if failure_counts[account['name']] > 0:
                print(f"✅ 账户 '{account['name']}' 已恢复，失败计数清零。")
                failure_counts[account['name']] = 0

        except Exception as e:
            # --- 4b. 如果是其他错误，则增加失败计数 ---
            print(f"⚠️ 账户 '{account['name']}' 发生未知错误: {e}")
            failure_counts[account['name']] += 1
            print(f"    -> 连续失败次数: {failure_counts[account['name']]}/{MAX_CONSECUTIVE_FAILURES}")

            if failure_counts[account['name']] >= MAX_CONSECUTIVE_FAILURES:
                print(f"🚨 警报！账户 '{account['name']}' 已连续失败 {MAX_CONSECUTIVE_FAILURES} 次，将被禁用！")
                account['status'] = 'disabled'

                alert_subject = f"账号失效警告：{account['name']}"
                alert_body = f"账号 '{account['name']}' (Email: {account['emailid']}) 已被自动禁用，最后一次错误: {e}"
                send_system_alert(alert_subject, alert_body)

        # --- 5. 等待下一个轮询周期 ---
        print(f"😴 等待 {config.POLLING_INTERVAL_SECONDS} 秒后，轮换到下一个账号...")
        time.sleep(config.POLLING_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_bot()