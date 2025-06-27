from notifier import send_email_alert


def run_test():
    """这是一个独立的测试函数"""
    print("--- 开始邮件发送模块独立测试 ---")

    # 模拟我们从Twitter抓取到了一个口令
    test_password = "test123456"
    test_tweet_url = "https://twitter.com/example/status/12345"

    print(f"模拟口令: {test_password}")
    print(f"模拟链接: {test_tweet_url}")

    # 调用邮件发送函数
    success = send_email_alert(test_password, test_tweet_url)

    if success:
        print("\n--- 测试成功 ---")
        print("请检查你的收件箱，确认是否收到测试邮件。")
    else:
        print("\n--- 测试失败 ---")
        print("请根据上面的错误提示检查你的配置。")


# 当我们直接运行这个文件时，才执行测试
if __name__ == "__main__":
    run_test()