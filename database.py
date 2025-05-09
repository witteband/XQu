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
    email_groups = db.Column(db.String(500), nullable=False)  # Komma-gescheiden e-mailadressen
    schedule = db.Column(db.String(100))  # Cron-expressie voor planning
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_run = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)  # Standaard ingesteld op False
    is_approved = db.Column(db.Boolean, default=False)  # Nieuw veld voor goedkeuringsstatus
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin die heeft goedgekeurd
    approved_at = db.Column(db.DateTime)  # Wanneer het is goedgekeurd
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Wie de query heeft gemaakt
    contact_person = db.Column(db.String(100))  # Contactpersoon voor de query
    contact_email = db.Column(db.String(120))  # Contact-e-mail voor de query
    contact_phone = db.Column(db.String(20))  # Contacttelefoon voor de query
    performance_metrics = db.relationship('QueryPerformanceMetrics', backref='query', lazy=True)

class QueryResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))  # success, error
    error_message = db.Column(db.Text)
    result_data = db.Column(db.Text)  # JSON-string van de query-resultaten

class QueryPerformanceMetrics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query_id = db.Column(db.Integer, db.ForeignKey('query.id'), nullable=False)
    execution_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Tijdmetrieken
    total_duration = db.Column(db.Float)  # Totale uitvoeringstijd (seconden)
    planning_time = db.Column(db.Float)   # Planningsduur (seconden)
    execution_time_db = db.Column(db.Float)  # Database uitvoeringstijd (seconden)
    
    # Bronnengebruik metrieken
    rows_processed = db.Column(db.Integer)  # Aantal verwerkte rijen
    memory_usage = db.Column(db.Float)      # Geheugengebruik (MB)
    cpu_usage = db.Column(db.Float)         # CPU-gebruik (%)
    
    # Query plan metrieken
    plan_type = db.Column(db.String(50))    # Query plantype (sequentieel scan, index scan, etc.)
    plan_rows = db.Column(db.Integer)       # Gepland aantal rijen
    actual_rows = db.Column(db.Integer)     # Werkelijk aantal rijen
    
    # Prestatie-waarschuwingen
    warnings = db.Column(db.Text)           # Prestatie-waarschuwingen (JSON-formaat)
    
    # Statistieken
    cache_hit_ratio = db.Column(db.Float)   # Cache-hitratio
    index_usage = db.Column(db.Float)
    
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