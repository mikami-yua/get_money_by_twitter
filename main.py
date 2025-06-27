# twitter_bot/main.py
import tweepy
import time
from datetime import datetime, timezone, timedelta

# 从同级目录的 config.py 文件中导入我们的配置
try:
    from . import config
except ImportError:
    import config


def run_bot():
    """程序主函数，使用 start_time 机制进行高精度、时效性过滤"""
    print("▶️ 启动Twitter监控机器人 (start_time 极限过滤模式)...")

    # 我们使用单账户配置
    account = config.ACCOUNTS[0]
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
            # 我们稍微多减一点时间（比如+60秒），作为网络延迟等的缓冲
            start_time_dt = now - timedelta(seconds=config.POLLING_INTERVAL_SECONDS + 60)
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
                for tweet in reversed(response.data):
                    print(f"\n--- 处理推文ID: {tweet.id} ---")
                    print(f"发布于: {tweet.created_at}")
                    print(f"内容: {tweet.text}")

                    # 在这里，我们不再需要客户端时效性过滤，因为服务器已经帮我们做好了

                    # password = extract_password(tweet.text)
                    # if password:
                    #     print(f"💰 成功提取到口令: {password}")
                    #     tweet_url = f"https://twitter.com/anyuser/status/{tweet.id}"
                    #     # send_email_alert(password, tweet_url)
                    # else:
                    #     print("🤷 未在该推文中发现格式化口令。")

            else:
                print("💨 本轮没有发现符合所有过滤条件的推文。")

        except Exception as e:
            print(f"❌ 发生错误: {e}")

        print(f"\n😴 等待 {config.POLLING_INTERVAL_SECONDS} 秒后进行下一轮搜索...")
        time.sleep(config.POLLING_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_bot()