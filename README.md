# Query Manager

Query Manager, farklı veritabanlarından sorgu çalıştırabilen ve sonuçları HTML formatında e-posta olarak gönderen bir web uygulamasıdır.

## Özellikler

- Farklı veritabanı bağlantıları oluşturma ve yönetme
- SQL sorguları oluşturma ve kaydetme
- Sorgu sonuçlarını HTML formatında e-posta olarak gönderme
- Sorgu sonuçlarını web arayüzünde görüntüleme
- Zamanlanmış sorgu çalıştırma (cron expression ile)
- RESTful API desteği

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. PostgreSQL veritabanını kurun ve yapılandırın.

3. `.env` dosyası oluşturun ve aşağıdaki değişkenleri ayarlayın:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=query_manager
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SECRET_KEY=your_secret_key
API_KEY=your_api_key_here
```

4. Uygulamayı başlatın:
```bash
python app.py
```

## Kullanım

1. Web tarayıcınızda `http://localhost:5000` adresine gidin
2. "New Connection" butonuna tıklayarak yeni bir veritabanı bağlantısı oluşturun
3. "New Query" butonuna tıklayarak yeni bir sorgu oluşturun
4. Sorguyu çalıştırmak için "Run" butonuna tıklayın
5. Sonuçları görüntülemek için "Results" butonuna tıklayın

## API Dokümantasyonu

Tüm API istekleri için `X-API-Key` header'ı gereklidir.

### Veritabanı Bağlantıları

#### Tüm Bağlantıları Listele
```http
GET /api/connections
```

#### Yeni Bağlantı Oluştur
```http
POST /api/connections
Content-Type: application/json

{
    "name": "My Database",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "pass"
}
```

### Sorgular

#### Tüm Sorguları Listele
```http
GET /api/queries
```

#### Yeni Sorgu Oluştur
```http
POST /api/queries
Content-Type: application/json

{
    "name": "Daily Report",
    "sql_query": "SELECT * FROM users",
    "connection_id": 1,
    "email_groups": "group1@example.com, group2@example.com",
    "schedule": "0 0 * * *"
}
```

#### Sorgu Çalıştır
```http
POST /api/queries/{query_id}/run
Content-Type: application/json

{
    "send_email": true
}
```

#### Sorgu Sonuçlarını Getir
```http
GET /api/queries/{query_id}/results
```

## Veritabanı Şeması

### DatabaseConnection
- id: Integer (Primary Key)
- name: String
- db_type: String
- host: String
- port: Integer
- database: String
- username: String
- password: String
- created_at: DateTime

### Query
- id: Integer (Primary Key)
- name: String
- sql_query: Text
- connection_id: Integer (Foreign Key)
- email_groups: String
- schedule: String
- created_at: DateTime
- last_run: DateTime
- is_active: Boolean

### QueryResult
- id: Integer (Primary Key)
- query_id: Integer (Foreign Key)
- execution_time: DateTime
- status: String
- error_message: Text
- result_data: Text

## Güvenlik Notları

- Veritabanı şifreleri ve SMTP kimlik bilgileri güvenli bir şekilde saklanmalıdır
- Üretim ortamında HTTPS kullanılmalıdır
- E-posta gönderimi için güvenli SMTP ayarları kullanılmalıdır
- Kullanıcı girişi ve yetkilendirme eklenmelidir
- API anahtarı güvenli bir şekilde saklanmalı ve düzenli olarak değiştirilmelidir # XQu
# XQu
