# Aktuelle Version der App auf Homeserver kopieren:

#### Dateien im Hauptverzeichnis kopieren

scp *.py *.txt *.sql *.json Dockerfile uli@192.168.178.201:/home/uli/docker/ngue-app/

#### Templates-Ordner kopieren

scp -r templates/ uli@192.168.178.201:/home/uli/docker/ngue-app/

#### Static-Ordner kopieren

scp -r static/ uli@192.168.178.201:/home/uli/docker/ngue-app/

### Database Zugriff lokal auf Mac
psql ngue_bvs_db

### Database-Zugriff auf Homeserver
docker exec -it ngue-postgres psql -U ngue_user -d ngue_db

### Spender und gesponserte Verse im DB
SELECT
    CONCAT(p.first_name, ' ', p.last_name) AS spender,
    d.created_at::date AS spende_datum,
    CONCAT(v.book, ' ', v.chapter, ',', v.verse) AS vers
  FROM persons p
  JOIN donations d ON p.id = d.person_id
  JOIN verses v ON d.verse_id = v.id
  ORDER BY d.created_at DESC;

### Gesamtzahl der gesponserten Verse
SELECT COUNT(*) FROM verses WHERE is_sponsored = true;


SELECT verse_id, payment_status, created_at
  FROM donations
  WHERE verse_id IN (
      SELECT id FROM verses
      WHERE (book = 'NEH' AND chapter = 7 AND verse =
  24)
         OR (book = '1KI' AND chapter = 5 AND verse =
  4)
         OR (book = '1KI' AND chapter = 17 AND verse =          22)
  );