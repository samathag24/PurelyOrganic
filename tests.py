import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os

load_dotenv()

def send_test_email():
    try:
        print("Connecting to SMTP server...")
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.set_debuglevel(1)  # Enable debug output
        print("Connected to SMTP server")

        print("Logging in...")
        server.login(os.getenv('EMAIL_HOST_USER'), os.getenv('EMAIL_HOST_PASSWORD'))
        print("Logged in")

        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_HOST_USER')
        msg['To'] = 'cherukurinimishachowdary@gmail.com'
        msg['Subject'] = 'Test Email'

        body = 'This is a test email sent from Python.'
        msg.attach(MIMEText(body, 'plain'))

        print("Sending email...")
        server.send_message(msg)
        server.quit()

        print('Email sent successfully')
    except Exception as e:
        print(f'Failed to send email: {e}')

if __name__ == '__main__':
    send_test_email()
