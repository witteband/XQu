import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import pandas as pd
from datetime import datetime

class EmailSender:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.username = Config.SMTP_USERNAME
        self.password = Config.SMTP_PASSWORD

    def create_html_table(self, data):
        """Convert query results to HTML table"""
        if isinstance(data, pd.DataFrame):
            return data.to_html(classes='table table-striped', index=False)
        return str(data)

    def send_query_results(self, to_emails, subject, query_name, results):
        """Send query results via email"""
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = f"Query Results: {subject}"

        # Create HTML content
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 10px; margin-bottom: 20px; }}
                    .table {{ border-collapse: collapse; width: 100%; }}
                    .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    .table th {{ background-color: #f2f2f2; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{query_name}</h2>
                        <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    {self.create_html_table(results)}
                    <div class="footer">
                        <p>This is an automated message. Please do not reply.</p>
                    </div>
                </div>
            </body>
        </html>
        """

        msg.attach(MIMEText(html_content, 'html'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False 