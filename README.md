# Query Manager

Query Manager is een webapplicatie waarmee u query's kunt uitvoeren op verschillende databases en de resultaten kunt verzenden als HTML-e-mail.

## Functies

- Aanmaken en beheren van verschillende databaseverbindingen
- SQL-query's maken en opslaan
- Query-resultaten verzenden als HTML-e-mail
- Query-resultaten bekijken in de webinterface
- Geplande query-uitvoering (met cron-expressie)
- RESTful API-ondersteuning
- Ondersteuning voor SQLite (standaard) en PostgreSQL databases

## Installatie

1. Maak een Python virtual environment aan en activeer deze:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

2. Installeer de benodigde Python-pakketten:
```bash
pip install -r requirements.txt
```

3. Maak een `.env` bestand aan en stel de volgende variabelen in:

Voor SQLite (standaard):
```
DATABASE_TYPE=sqlite
SQLITE_DB_PATH=data/query_manager.db
```

Voor PostgreSQL:
```
DATABASE_TYPE=postgresql
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=query_manager
POSTGRES_USER=uw_gebruikersnaam
POSTGRES_PASSWORD=uw_wachtwoord
```

Algemene instellingen:
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=uw_email@gmail.com
SMTP_PASSWORD=uw_app_wachtwoord
SECRET_KEY=uw_geheime_sleutel
API_KEY=uw_api_sleutel_hier
```

4. Start de applicatie:
```bash
python app.py
```

## Database Configuratie

### SQLite (Standaard)
- SQLite wordt standaard gebruikt en vereist geen extra installatie
- De database wordt opgeslagen in `data/query_manager.db`
- De database blijft behouden, zelfs als de server wordt afgesloten
- Ideaal voor ontwikkeling en kleine tot middelgrote implementaties

### PostgreSQL
- Voor grotere implementaties of wanneer meerdere gebruikers gelijktijdig toegang nodig hebben
- Vereist een geïnstalleerde PostgreSQL-server
- Configureer de verbinding via de `.env` bestand

## Gebruik

1. Ga naar `http://localhost:5000` in uw webbrowser
2. Klik op de "Nieuwe Verbinding" knop om een nieuwe databaseverbinding aan te maken
3. Klik op de "Nieuwe Query" knop om een nieuwe query aan te maken
4. Klik op de "Uitvoeren" knop om de query uit te voeren
5. Klik op de "Resultaten" knop om de resultaten te bekijken

## API Documentatie

Voor alle API-verzoeken is de `X-API-Key` header vereist.

### Databaseverbindingen

#### Alle Verbindingen Weergeven
```http
GET /api/connections
```

#### Nieuwe Verbinding Aanmaken
```http
POST /api/connections
Content-Type: application/json

{
    "name": "Mijn Database",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "gebruiker",
    "password": "wachtwoord"
}
```

### Query's

#### Alle Query's Weergeven
```http
GET /api/queries
```

#### Nieuwe Query Aanmaken
```http
POST /api/queries
Content-Type: application/json

{
    "name": "Dagelijks Rapport",
    "sql_query": "SELECT * FROM users",
    "connection_id": 1,
    "email_groups": "groep1@voorbeeld.com, groep2@voorbeeld.com",
    "schedule": "0 0 * * *"
}
```

#### Query Uitvoeren
```http
POST /api/queries/{query_id}/run
Content-Type: application/json

{
    "send_email": true
}
```

#### Query-resultaten Ophalen
```http
GET /api/queries/{query_id}/results
```

## Databaseschema

### DatabaseConnection
- id: Integer (Primaire Sleutel)
- name: String
- db_type: String
- host: String
- port: Integer
- database: String
- username: String
- password: String
- created_at: DateTime

### Query
- id: Integer (Primaire Sleutel)
- name: String
- sql_query: Text
- connection_id: Integer (Buitenlandse Sleutel)
- email_groups: String
- schedule: String
- created_at: DateTime
- last_run: DateTime
- is_active: Boolean

### QueryResult
- id: Integer (Primaire Sleutel)
- query_id: Integer (Buitenlandse Sleutel)
- execution_time: DateTime
- status: String
- error_message: Text
- result_data: Text

## Beveiligingsnotities

- Database-wachtwoorden en SMTP-inloggegevens moeten veilig worden opgeslagen
- Gebruik HTTPS in productieomgevingen
- Gebruik veilige SMTP-instellingen voor e-mailverzending
- Gebruikersauthenticatie en autorisatie moeten worden toegevoegd
- API-sleutel moet veilig worden opgeslagen en regelmatig worden gewijzigd
- Voor SQLite: Zorg ervoor dat de database-bestand niet toegankelijk is via de webserver
