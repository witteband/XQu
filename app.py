from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import db, DatabaseConnection, Query, QueryResult, QueryPerformanceMetrics, User
from email_sender import EmailSender
from config import Config
import pandas as pd
import json
from datetime import datetime
import sqlalchemy as sa
from functools import wraps
import psutil
import time
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import oracledb
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
email_sender = EmailSender()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Role-based access control decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            # Admin users have access to all roles
            if current_user.role == 'admin' or current_user.role in roles:
                return f(*args, **kwargs)
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('index'))
        return decorated_function
    return decorator

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    if current_user.is_admin():
        queries = Query.query.all()
    elif current_user.is_operator():
        queries = Query.query.filter_by(is_active=True).all()
    else:
        queries = Query.query.filter_by(creator_id=current_user.id).all()
    
    connections = DatabaseConnection.query.all()
    return render_template('index.html', connections=connections, queries=queries)

@app.route('/connection/new', methods=['GET', 'POST'])
def new_connection():
    if request.method == 'POST':
        connection = DatabaseConnection(
            name=request.form['name'],
            db_type=request.form['db_type'],
            host=request.form['host'],
            port=int(request.form['port']),
            database=request.form['database'],
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(connection)
        db.session.commit()
        flash('Database connection added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('new_connection.html')

@app.route('/query/new', methods=['GET', 'POST'])
@login_required
@role_required(['user', 'admin'])
def new_query():
    if request.method == 'POST':
        query = Query(
            name=request.form['name'],
            sql_query=request.form['sql_query'],
            connection_id=int(request.form['connection_id']),
            email_groups=request.form['email_groups'],
            schedule=request.form['schedule'],
            creator_id=current_user.id,
            contact_person=request.form['contact_person'],
            contact_email=request.form['contact_email'],
            contact_phone=request.form['contact_phone'],
            is_active=False,
            is_approved=False
        )
        db.session.add(query)
        db.session.commit()
        flash('Query added successfully! Waiting for admin approval.', 'success')
        return redirect(url_for('index'))
    connections = DatabaseConnection.query.all()
    return render_template('new_query.html', connections=connections)

@app.route('/query/approve/<int:query_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def approve_query(query_id):
    query = Query.query.get_or_404(query_id)
    query.is_approved = True
    query.is_active = True
    query.approved_by = current_user.id
    query.approved_at = datetime.utcnow()
    db.session.commit()
    flash('Query approved successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/query/reject/<int:query_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def reject_query(query_id):
    query = Query.query.get_or_404(query_id)
    query.is_approved = False
    query.is_active = False
    db.session.commit()
    flash('Query rejected.', 'info')
    return redirect(url_for('index'))

def get_db_engine(connection):
    """Veritabanı bağlantı URL'sini oluştur"""
    if connection.db_type.lower() == 'oracle':
        # Oracle için özel bağlantı URL'si
        return sa.create_engine(
            f"oracle+oracledb://{connection.username}:{connection.password}@{connection.host}:{connection.port}/?service_name={connection.database}",
            thick_mode=None
        )
    elif connection.db_type.lower() == 'postgresql':
        # PostgreSQL için standart bağlantı URL'si
        return sa.create_engine(
            f"postgresql://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
        )
    else:
        raise ValueError(f"Desteklenmeyen veritabanı tipi: {connection.db_type}")

def collect_performance_metrics(engine, query, start_time):
    """Sorgu performans metriklerini topla"""
    metrics = {}
    
    # Toplam süre
    total_duration = time.time() - start_time
    metrics['total_duration'] = total_duration
    
    # Veritabanı tipine göre performans metriklerini topla
    if 'oracle' in str(engine.url):
        with engine.connect() as conn:
            # Oracle için EXPLAIN PLAN kullan
            plan_query = f"EXPLAIN PLAN FOR {query}"
            conn.execute(plan_query)
            
            # Plan detaylarını al
            plan_details = conn.execute("""
                SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, NULL, 'ALL'))
            """).fetchall()
            
            # Plan tipini belirle
            plan_type = 'Unknown'
            for row in plan_details:
                if 'TABLE ACCESS' in str(row):
                    plan_type = 'Table Access'
                elif 'INDEX' in str(row):
                    plan_type = 'Index Scan'
            
            metrics['plan_type'] = plan_type
            
            # Oracle istatistiklerini al
            stats = conn.execute("""
                SELECT name, value 
                FROM v$statname n, v$mystat s 
                WHERE n.statistic# = s.statistic#
            """).fetchall()
            
            # Önbellek isabet oranını hesapla
            buffer_cache_hits = next((s[1] for s in stats if 'buffer cache hit ratio' in s[0].lower()), 0)
            metrics['cache_hit_ratio'] = buffer_cache_hits
            
            # Uyarıları belirle
            warnings = []
            if plan_type == 'Table Access':
                warnings.append("Sequential scan kullanılıyor - indeks eklenebilir")
            if buffer_cache_hits < 80:
                warnings.append("Düşük önbellek isabet oranı")
            metrics['warnings'] = json.dumps(warnings)
            
    elif 'postgresql' in str(engine.url):
        with engine.connect() as conn:
            # PostgreSQL için EXPLAIN ANALYZE kullan
            plan_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            plan_result = conn.execute(plan_query).scalar()
            plan_data = json.loads(plan_result)[0]
            
            # Planlama ve çalıştırma süreleri
            metrics['planning_time'] = plan_data.get('Planning Time', 0) / 1000  # ms to s
            metrics['execution_time_db'] = plan_data.get('Execution Time', 0) / 1000  # ms to s
            
            # Satır sayıları
            metrics['plan_rows'] = plan_data.get('Plan', {}).get('Plan Rows', 0)
            metrics['actual_rows'] = plan_data.get('Plan', {}).get('Actual Rows', 0)
            
            # Plan tipi
            metrics['plan_type'] = plan_data.get('Plan', {}).get('Node Type', '')
            
            # Önbellek ve indeks kullanımı
            shared_hits = plan_data.get('Shared Hit Blocks', 0)
            shared_reads = plan_data.get('Shared Read Blocks', 0)
            total_blocks = shared_hits + shared_reads
            metrics['cache_hit_ratio'] = (shared_hits / total_blocks * 100) if total_blocks > 0 else 0
            
            # Performans uyarıları
            warnings = []
            if metrics['plan_type'] == 'Seq Scan':
                warnings.append("Sequential scan kullanılıyor - indeks eklenebilir")
            if metrics['cache_hit_ratio'] < 80:
                warnings.append("Düşük önbellek isabet oranı")
            metrics['warnings'] = json.dumps(warnings)
    
    # Sistem kaynak kullanımı
    process = psutil.Process()
    metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
    metrics['cpu_usage'] = process.cpu_percent()
    
    return metrics

@app.route('/query/run/<int:query_id>')
@login_required
@role_required(['user', 'operator', 'admin'])
def run_query(query_id):
    query = Query.query.get_or_404(query_id)
    
    # Yetki kontrolü - Admin tüm sorguları çalıştırabilir
    if not current_user.is_admin() and query.creator_id != current_user.id:
        flash('You do not have permission to run this query.', 'error')
        return redirect(url_for('index'))
    
    # Onay kontrolü - Admin onaylı olmayan sorguları da çalıştırabilir
    if not query.is_approved and not current_user.is_admin():
        flash('This query is not approved yet.', 'error')
        return redirect(url_for('index'))
    
    connection = DatabaseConnection.query.get(query.connection_id)
    
    try:
        # Veritabanı bağlantısını oluştur
        engine = get_db_engine(connection)
        
        # Performans metriklerini topla
        start_time = time.time()
        
        # Sorguyu çalıştır
        with engine.connect() as conn:
            result = pd.read_sql(query.sql_query, conn)
        
        # Performans metriklerini kaydet
        metrics = collect_performance_metrics(engine, query.sql_query, start_time)
        performance_metrics = QueryPerformanceMetrics(
            query_id=query.id,
            total_duration=metrics['total_duration'],
            planning_time=metrics.get('planning_time'),
            execution_time_db=metrics.get('execution_time_db'),
            rows_processed=len(result),
            memory_usage=metrics['memory_usage'],
            cpu_usage=metrics['cpu_usage'],
            plan_type=metrics.get('plan_type'),
            plan_rows=metrics.get('plan_rows'),
            actual_rows=metrics.get('actual_rows'),
            warnings=metrics.get('warnings'),
            cache_hit_ratio=metrics.get('cache_hit_ratio')
        )
        db.session.add(performance_metrics)
        
        # Sonucu kaydet
        query_result = QueryResult(
            query_id=query.id,
            status='success',
            result_data=result.to_json()
        )
        db.session.add(query_result)
        
        # Son çalıştırma zamanını güncelle
        query.last_run = datetime.utcnow()
        db.session.commit()
        
        # E-posta gönder
        email_groups = [email.strip() for email in query.email_groups.split(',')]
        email_sender.send_query_results(
            email_groups,
            query.name,
            query.name,
            result
        )
        
        flash('Query executed and results sent successfully!', 'success')
    except Exception as e:
        query_result = QueryResult(
            query_id=query.id,
            status='error',
            error_message=str(e),
            error_contact={
                'person': query.contact_person,
                'email': query.contact_email,
                'phone': query.contact_phone
            }
        )
        db.session.add(query_result)
        db.session.commit()
        flash(f'Error executing query: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/query/results/<int:query_id>')
def query_results(query_id):
    results = QueryResult.query.filter_by(query_id=query_id).order_by(QueryResult.execution_time.desc()).all()
    return render_template('query_results.html', results=results)

@app.route('/query/metrics/<int:query_id>')
@login_required
@role_required(['user', 'operator', 'admin'])
def query_metrics(query_id):
    query = Query.query.get_or_404(query_id)
    
    # Yetki kontrolü - Admin tüm metrikleri görebilir
    if not current_user.is_admin() and query.creator_id != current_user.id:
        flash('You do not have permission to view these metrics.', 'error')
        return redirect(url_for('index'))
    
    metrics = QueryPerformanceMetrics.query.filter_by(query_id=query_id).order_by(QueryPerformanceMetrics.execution_time.desc()).all()
    return render_template('query_metrics.html', query=query, metrics=metrics)

@app.route('/query/advanced-report/<int:query_id>')
@login_required
@role_required(['user', 'operator', 'admin'])
def advanced_report(query_id):
    query = Query.query.get_or_404(query_id)
    
    # Yetki kontrolü - Admin tüm raporları görebilir
    if not current_user.is_admin() and query.creator_id != current_user.id:
        flash('You do not have permission to view this report.', 'error')
        return redirect(url_for('index'))
    
    metrics = QueryPerformanceMetrics.query.filter_by(query_id=query_id).order_by(QueryPerformanceMetrics.execution_time.desc()).all()
    
    # Performans skoru hesaplama
    for metric in metrics:
        execution_score = max(0, 100 - (metric.total_duration * 10))
        resource_score = max(0, 100 - ((metric.memory_usage / 1000) + (metric.cpu_usage / 2)))
        cache_score = metric.cache_hit_ratio or 0
        metric.performance_score = (execution_score * 0.4 + resource_score * 0.3 + cache_score * 0.3)
    
    return render_template('advanced_report.html', query=query, metrics=metrics)

# Admin paneli route'u
@app.route('/admin')
@login_required
@role_required(['admin'])
def admin_panel():
    pending_queries = Query.query.filter_by(is_approved=False).all()
    active_queries = Query.query.filter_by(is_active=True).all()
    users = User.query.all()
    return render_template('admin_panel.html', 
                         pending_queries=pending_queries,
                         active_queries=active_queries,
                         users=users)

# Operator paneli route'u
@app.route('/operator')
@login_required
@role_required(['operator'])
def operator_panel():
    active_queries = Query.query.filter_by(is_active=True).all()
    error_queries = QueryResult.query.filter_by(status='error').order_by(QueryResult.execution_time.desc()).all()
    return render_template('operator_panel.html',
                         active_queries=active_queries,
                         error_queries=error_queries)

# API Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key and api_key == Config.API_KEY:
            return f(*args, **kwargs)
        return jsonify({"error": "Invalid API key"}), 401
    return decorated

# API Endpoints
@app.route('/api/connections', methods=['GET'])
@require_api_key
def api_get_connections():
    connections = DatabaseConnection.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'db_type': c.db_type,
        'host': c.host,
        'port': c.port,
        'database': c.database,
        'username': c.username,
        'created_at': c.created_at.isoformat()
    } for c in connections])

@app.route('/api/connections', methods=['POST'])
@require_api_key
def api_create_connection():
    data = request.get_json()
    try:
        connection = DatabaseConnection(
            name=data['name'],
            db_type=data['db_type'],
            host=data['host'],
            port=int(data['port']),
            database=data['database'],
            username=data['username'],
            password=data['password']
        )
        db.session.add(connection)
        db.session.commit()
        return jsonify({
            'id': connection.id,
            'message': 'Connection created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/queries', methods=['GET'])
@require_api_key
def api_get_queries():
    queries = Query.query.all()
    return jsonify([{
        'id': q.id,
        'name': q.name,
        'connection_id': q.connection_id,
        'email_groups': q.email_groups,
        'schedule': q.schedule,
        'created_at': q.created_at.isoformat(),
        'last_run': q.last_run.isoformat() if q.last_run else None,
        'is_active': q.is_active
    } for q in queries])

@app.route('/api/queries', methods=['POST'])
@require_api_key
def api_create_query():
    data = request.get_json()
    try:
        query = Query(
            name=data['name'],
            sql_query=data['sql_query'],
            connection_id=int(data['connection_id']),
            email_groups=data['email_groups'],
            schedule=data.get('schedule')
        )
        db.session.add(query)
        db.session.commit()
        return jsonify({
            'id': query.id,
            'message': 'Query created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/queries/<int:query_id>/run', methods=['POST'])
@require_api_key
def api_run_query(query_id):
    query = Query.query.get_or_404(query_id)
    connection = DatabaseConnection.query.get(query.connection_id)
    
    try:
        # Create database connection URL
        db_url = f"{connection.db_type}://{connection.username}:{connection.password}@{connection.host}:{connection.port}/{connection.database}"
        engine = sa.create_engine(db_url)
        
        # Execute query
        with engine.connect() as conn:
            result = pd.read_sql(query.sql_query, conn)
        
        # Store result
        query_result = QueryResult(
            query_id=query.id,
            status='success',
            result_data=result.to_json()
        )
        db.session.add(query_result)
        
        # Update last run time
        query.last_run = datetime.utcnow()
        db.session.commit()
        
        # Send email if requested
        if request.json.get('send_email', True):
            email_groups = [email.strip() for email in query.email_groups.split(',')]
            email_sender.send_query_results(
                email_groups,
                query.name,
                query.name,
                result
            )
        
        return jsonify({
            'status': 'success',
            'message': 'Query executed successfully',
            'result': json.loads(result.to_json())
        })
    except Exception as e:
        query_result = QueryResult(
            query_id=query.id,
            status='error',
            error_message=str(e)
        )
        db.session.add(query_result)
        db.session.commit()
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/queries/<int:query_id>/results', methods=['GET'])
@require_api_key
def api_get_query_results(query_id):
    results = QueryResult.query.filter_by(query_id=query_id).order_by(QueryResult.execution_time.desc()).all()
    return jsonify([{
        'id': r.id,
        'execution_time': r.execution_time.isoformat(),
        'status': r.status,
        'error_message': r.error_message,
        'result_data': json.loads(r.result_data) if r.result_data else None
    } for r in results])

@app.route('/api/queries/<int:query_id>/metrics', methods=['GET'])
@require_api_key
def api_get_query_metrics(query_id):
    metrics = QueryPerformanceMetrics.query.filter_by(query_id=query_id).order_by(QueryPerformanceMetrics.execution_time.desc()).all()
    return jsonify([m.to_dict() for m in metrics])

@app.route('/database/connections')
@login_required
@role_required(['admin'])
def database_connections():
    connections = DatabaseConnection.query.all()
    return render_template('database_connections.html', connections=connections)

@app.route('/connection/new', methods=['POST'])
@login_required
@role_required(['admin'])
def new_connection():
    try:
        connection = DatabaseConnection(
            name=request.form['name'],
            db_type=request.form['db_type'],
            host=request.form['host'],
            port=int(request.form['port']),
            database=request.form['database'],
            username=request.form['username'],
            password=request.form['password']
        )
        db.session.add(connection)
        db.session.commit()
        flash('Database connection added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding database connection: {str(e)}', 'error')
    return redirect(url_for('database_connections'))

@app.route('/api/connections/<int:connection_id>/test', methods=['POST'])
@login_required
@role_required(['admin'])
def test_connection(connection_id):
    connection = DatabaseConnection.query.get_or_404(connection_id)
    try:
        engine = get_db_engine(connection)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/connections/<int:connection_id>', methods=['DELETE'])
@login_required
@role_required(['admin'])
def delete_connection(connection_id):
    connection = DatabaseConnection.query.get_or_404(connection_id)
    try:
        # Bağlantıyı kullanan sorguları kontrol et
        if connection.queries:
            return jsonify({
                'status': 'error',
                'error': 'Cannot delete connection that is being used by queries'
            })
        
        db.session.delete(connection)
        db.session.commit()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 