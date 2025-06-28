from notifier import send_email_alert
from parser import extract_password
RUN_EMAIL_TEST = False

def test_email():
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


# 你可以不断在这里添加新的、真实的、刁钻的推文样本来挑战你的解析器
TEST_CASES = [
    # --- 应该成功匹配的案例 ---
    {"text": "口令是:hongbao123, 快来领", "expected": "hongbao123"},
    {"text": "新年快乐！口令：HAPPY2025", "expected": "happy2025"},
    {"text": "支付宝:caiyuan_gun_gun", "expected": "caiyuan_gun_gun"},
    {"text": "送个红包，口令（88888888）", "expected": "88888888"},
    {"text": "口令「testpassword」", "expected": "testpassword"},
    {"text": "我的天，居然中了，口令是: aBcDeFg", "expected": "abcdefg"},
    {"text": "87654321", "expected": "87654321"},
    {"text":"测试一下口令红包的识别能力：23259006","expected":"23259006"},

    # --- 不应该成功匹配的案例 (我们期望返回 None) ---
    {"text": "谢谢老板的口令红包！", "expected": None},
    {"text": "谁有口令红包呀，求一个", "expected": None},
    {"text": "视频打包，仅限口令红包，需要的私信", "expected": None},
    {"text": "支付宝代收服务，联系TG", "expected": None},
    {"text": "口令: 12345", "expected": None},
    {"text": "我的支付宝账号是 an_example", "expected": None},
    {"text": "口令是: 带中文的口令", "expected": None},
]


def test_parser():
    """独立的解析器单元测试函数"""
    print("=============================================")
    print("          1. 开始运行解析器单元测试          ")
    print("=============================================")

    passed_count = 0
    failed_count = 0

    for i, case in enumerate(TEST_CASES):
        tweet_text = case['text']
        expected_password = case['expected']

        # 调用我们真正要测试的函数
        actual_password = extract_password(tweet_text)

        # 检查结果是否符合预期
        if actual_password == expected_password:
            print(f"✅ PASS: 测试用例 {i + 1} 通过!")
            passed_count += 1
        else:
            print(f"❌ FAIL: 测试用例 {i + 1} 失败!")
            print(f"   - 输入文本: '{tweet_text}'")
            print(f"   - 期望结果: '{expected_password}'")
            print(f"   - 实际得到: '{actual_password}'")
            failed_count += 1

    print("\n--- 解析器测试总结 ---")
    print(f"总计: {len(TEST_CASES)}, 通过: {passed_count}, 失败: {failed_count}")

    # 如果有失败的测试，整个函数返回False
    return failed_count == 0


# 当我们直接运行这个文件时，才执行测试
if __name__ == "__main__":
    # 首先，总是运行解析器的测试
    parser_ok = test_parser()

    # 然后，根据开关决定是否运行邮件测试
    if RUN_EMAIL_TEST:
        test_email()