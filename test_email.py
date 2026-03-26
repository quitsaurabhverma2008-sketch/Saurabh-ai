import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config
smtp_email = "saurabh.ai.dev@gmail.com"
smtp_password = "hvjjxpqfspfcsqkm"
smtp_server = "smtp.gmail.com"
smtp_port = 587

test_email = "quitsaurabhverma@2008@gmail.com"

print(f"Testing email...")
print(f"SMTP Email: {smtp_email}")
print(f"Password length: {len(smtp_password)}")
print(f"Test recipient: {test_email}")

try:
    print("\nConnecting to SMTP server...")
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    print("TLS started...")
    
    print("Attempting login...")
    server.login(smtp_email, smtp_password)
    print("Login successful!")
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = smtp_email
    msg['To'] = test_email
    msg['Subject'] = "Saurabh AI - Test Email"
    
    body = "Test email from Saurabh AI!"
    msg.attach(MIMEText(body, 'plain'))
    
    print("Sending email...")
    server.send_message(msg)
    print("✅ Email sent successfully!")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ AUTH ERROR: {e}")
    print("\nPossible causes:")
    print("1. App Password is incorrect")
    print("2. 2-Factor Authentication not enabled on Gmail")
    print("3. Less Secure App Access needs to be enabled (not recommended)")
    print("\nTo fix:")
    print("- Go to Gmail → Security → 2-Step Verification")
    print("- Enable 2FA, then generate new App Password")
    print("- Use the new 16-character password (no spaces)")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP ERROR: {e}")
    
except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}: {e}")
