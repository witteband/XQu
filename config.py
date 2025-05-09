import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database type selection (sqlite or postgresql)
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')
    
    # SQLite database settings
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'data/query_manager.db')
    
    # PostgreSQL database-instellingen
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'query_manager')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')
    
    # E-mail instellingen
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    # API instellingen
    API_KEY = os.getenv('API_KEY', 'your-api-key-here')
    
    # Flask instellingen
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # Database URI configuration
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if self.DATABASE_TYPE == 'sqlite':
            # Ensure the data directory exists
            os.makedirs(os.path.dirname(self.SQLITE_DB_PATH), exist_ok=True)
            return f"sqlite:///{self.SQLITE_DB_PATH}"
        else:
            return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False 