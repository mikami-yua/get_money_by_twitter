# notifier.py (v2 - 增加了重试机制的最终版)
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header

# 导入配置
try:
    from . import config
except ImportError:
    import config

# --- 新增的重试配置 ---
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY_SECONDS = 5  # 每次重试的间隔时间（秒）


# --- 用于发送口令红包的函数 (保持不变) ---
def send_red_packet_alert(password: str, original_tweet_url: str):
    subject = f"发现新的红包口令: {password}"
    body = f"口令: {password}\n链接: {original_tweet_url}\n\n请尽快使用！"
    # 调用通用的邮件发送器
    _send_email(subject, body)


# --- 新增的、用于发送系统警报的函数 ---
def send_system_alert(alert_subject: str, alert_body: str):
    subject = f"【机器人告警】{alert_subject}"
    body = f"这是一个来自Twitter监控机器人的自动告警：\n\n{alert_body}"
    # 调用通用的邮件发送器
    _send_email(subject, body)


# --- 内部通用的邮件发送逻辑 ---
def _send_email(subject: str, body: str):
    """通用的邮件发送函数，包含重试逻辑"""
    if not config.EMAIL_CONFIG["use_email"]:
        print("邮件发送功能已禁用。")
        return False

    conf = config.EMAIL_CONFIG
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(f"监控机器人 <{conf['sender_email']}>", 'utf-8')
    msg['To'] = Header(f"管理员 <{conf['receiver_email']}>", 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n[邮件发送] 正在进行第 {attempt}/{MAX_RETRIES} 次尝试...")
        try:
            with smtplib.SMTP_SSL(conf['smtp_server'], conf['port'], timeout=10) as server:
                server.login(conf['sender_email'], conf['password'])
                server.sendmail(conf['sender_email'], [conf['receiver_email']], msg.as_string())
            print(f"✅ [邮件发送] 成功！邮件已发送到 {conf['receiver_email']}。")
            return True
        except Exception as e:
            print(f"⚠️ [邮件发送] 第 {attempt} 次尝试失败，错误: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                print("❌ [邮件发送] 已达到最大重试次数，彻底失败。")
    return False