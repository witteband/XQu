from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'user', 'operator', 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    queries = db.relationship('Query', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_operator(self):
        return self.role == 'operator'

    def is_user(self):
        return self.role == 'user'

class DatabaseConnection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    db_type = db.Column(db.String(50), nullable=False)  # postgresql, mysql, oracle, etc.
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    database = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    queries = db.relationship('Query', backref='connection', lazy=True)

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sql_query = db.Column(db.Text, nullable=False)
    connection_id = db.Column(db.Integer, db.ForeignKey('database_connection.id'), nullable=False)
    email_groups = db.Column(db.String(500), nullable=False)  # Comma-separated email addresses
    schedule = db.Column(db.String(100))  # Cron expression for scheduling
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_run = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)  # Changed to False by default
    is_approved = db.Column(db.Boolean, default=False)  # New field for approval status
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who approved
    approved_at = db.Column(db.DateTime)  # When it was approved
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Who created the query
    contact_person = db.Column(db.String(100))  # Contact person for the query
    contact_email = db.Column(db.String(120))  # Contact email for the query
    contact_phone = db.Column(db.String(20))  # Contact phone for the query
    performance_metrics = db.relationship('QueryPerformanceMetrics', backref='query', lazy=True)

class QueryResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))  # success, error
    error_message = db.Column(db.Text)
    result_data = db.Column(db.Text)  # JSON string of the query results

class QueryPerformanceMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Zaman metrikleri
    total_duration = db.Column(db.Float)  # Toplam çalışma süresi (saniye)
    planning_time = db.Column(db.Float)   # Planlama süresi (saniye)
    execution_time_db = db.Column(db.Float)  # Veritabanı çalıştırma süresi (saniye)
    
    # Kaynak kullanım metrikleri
    rows_processed = db.Column(db.Integer)  # İşlenen satır sayısı
    memory_usage = db.Column(db.Float)      # Bellek kullanımı (MB)
    cpu_usage = db.Column(db.Float)         # CPU kullanımı (%)
    
    # Sorgu planı metrikleri
    plan_type = db.Column(db.String(50))    # Sorgu planı tipi (sequential scan, index scan, etc.)
    plan_rows = db.Column(db.Integer)       # Planlanan satır sayısı
    actual_rows = db.Column(db.Integer)     # Gerçek satır sayısı
    
    # Performans uyarıları
    warnings = db.Column(db.Text)           # Performans uyarıları (JSON formatında)
    
    # İstatistikler
    cache_hit_ratio = db.Column(db.Float)   # Önbellek isabet oranı
    index_usage = db.Column(db.Float)       # İndeks kullanım oranı
    
    def to_dict(self):
        return {
            'id': self.id,
            'query_id': self.query_id,
            'execution_time': self.execution_time.isoformat(),
            'total_duration': self.total_duration,
            'planning_time': self.planning_time,
            'execution_time_db': self.execution_time_db,
            'rows_processed': self.rows_processed,
            'memory_usage': self.memory_usage,
            'cpu_usage': self.cpu_usage,
            'plan_type': self.plan_type,
            'plan_rows': self.plan_rows,
            'actual_rows': self.actual_rows,
            'warnings': self.warnings,
            'cache_hit_ratio': self.cache_hit_ratio,
            'index_usage': self.index_usage
        } 