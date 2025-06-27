# twitter_bot/notifier.py
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 导入配置。假设config.py在同一目录下
try:
    from . import config
except ImportError:
    import config


def send_email_alert(password: str, original_tweet_url: str):
    """根据配置发送邮件通知"""
    if not config.EMAIL_CONFIG["use_email"]:
        print("邮件发送功能已在config.py中禁用。")
        return False

    conf = config.EMAIL_CONFIG

    subject = f"发现新的红包口令: {password}"
    body = f"""
    已成功从Twitter上提取到新的红包口令！

    口令: {password}

    原始推文链接: {original_tweet_url}

    请尽快使用！
    """

    # 构造邮件对象
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(f"红包监控机器人 <{conf['sender_email']}>", 'utf-8')
    msg['To'] = Header(f"幸运的你 <{conf['receiver_email']}>", 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        # 使用SSL加密方式连接SMTP服务器
        print(f"正在连接到邮件服务器 {conf['smtp_server']}...")
        with smtplib.SMTP_SSL(conf['smtp_server'], conf['port']) as server:
            print("正在登录邮箱...")
            server.login(conf['sender_email'], conf['password'])
            print("正在发送邮件...")
            server.sendmail(conf['sender_email'], [conf['receiver_email']], msg.as_string())
        print(f"✅ 成功发送测试邮件到 {conf['receiver_email']}！")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ 邮件发送失败：SMTP认证失败！请检查你的邮箱地址和16位应用专用密码是否正确。")
        return False
    except Exception as e:
        print(f"❌ 邮件发送失败，发生未知错误: {e}")
        return False