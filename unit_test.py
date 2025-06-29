from notifier import send_red_packet_alert, send_system_alert
from parser import extract_password
RUN_EMAIL_TEST = True
import time

# --- 测试配置 ---
TEST_RED_PACKET_EMAIL = False  # 是否测试发送“口令红包”邮件
TEST_SYSTEM_ALERT_EMAIL = True   # 是否测试发送“系统告警”邮件

def test_red_packet_email_sending():
    """测试发送“口令红包”通知邮件"""
    print("\n=============================================")
    print("          2a. 开始测试 [口令红包] 邮件发送        ")
    print("=============================================")
    test_password = "test_red_packet_123"
    test_tweet_url = "https://twitter.com/example/status/12345"
    print(f"模拟发送... 口令: {test_password}")
    return send_red_packet_alert(test_password, test_tweet_url)


# --- !! 新增的测试函数 !! ---
def test_system_alert_email_sending():
    """测试发送“系统告警”通知邮件"""
    print("\n=============================================")
    print("          2b. 开始测试 [系统告警] 邮件发送        ")
    print("=============================================")
    test_subject = "账号测试警告"
    test_body = "这是一个测试，用于验证系统警告邮件功能是否正常。\n如果收到这封邮件，说明功能工作正常。"
    print(f"模拟发送... 告警主题: {test_subject}")
    return send_system_alert(test_subject, test_body)


# --- 测试用例库 (已更新) ---
TEST_CASES = [
    # --- !! 你今天带来的新案例 !! ---
    {"text": "支付宝口令红包31097309，大家积极点关注，关注后续福利。", "expected": "31097309"},
    {"text": "测试一下口令红包的识别能力：23259006", "expected": "23259006"},
    {"text":"坦言： “扬州毕竟是我的出生地，对扬州还是有感情的。当初扬州队联系我的时候。口令红包：97413963 https://t.co/B....","expected": "97413963"},

    # --- 之前能通过的案例 ---
    {"text": "口令是:hongbao123, 快来领", "expected": "hongbao123"},
    {"text": "支付宝:caiyuan_gun_gun", "expected": "caiyuan_gun_gun"},
    {"text": "口令「testpassword」", "expected": "testpassword"},
    {"text": "87654321", "expected": "87654321"},

    # --- 新增的中文口令案例 ---
    {"text": "我发个口令红包:大家新年好", "expected": "大家新年好"},
    {"text": "口令红包：恭喜发财", "expected": "恭喜发财"},

    # --- 应该失败的案例 ---
    {"text": "谢谢老板的口令红包！", "expected": None},
    {"text": "谁有口令红包呀，求一个", "expected": None},
    {"text": "口令红包已发,注意查收", "expected": None},
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
        parser_ok = test_parser()

        # 根据开关决定是否运行“口令红包”邮件测试
        if TEST_RED_PACKET_EMAIL:
            red_packet_email_ok = test_red_packet_email_sending()
        else:
            print("\n[跳过] 口令红包邮件测试已禁用。")
            red_packet_email_ok = True

        # 根据开关决定是否运行“系统告警”邮件测试
        if TEST_SYSTEM_ALERT_EMAIL:
            system_alert_email_ok = test_system_alert_email_sending()
        else:
            print("\n[跳过] 系统告警邮件测试已禁用。")
            system_alert_email_ok = True

        # 最终报告
        print("\n=============================================")
        print("                最终测试报告                 ")
        print("=============================================")
        if parser_ok and red_packet_email_ok and system_alert_email_ok:
            print("🎉🎉🎉 恭喜！所有已执行的测试均已通过！🎉🎉🎉")
        else:
            print("🔥 注意：部分测试失败，请检查上面的日志。🔥")
        print("=============================================")