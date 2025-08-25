# Aktuelle Version der App auf Homeserver kopieren:

#### Dateien im Hauptverzeichnis kopieren

scp *.py *.txt *.sql *.json Dockerfile uli@192.168.178.201:/home/uli/docker/ngue-app/

#### Templates-Ordner kopieren

scp -r templates/ uli@192.168.178.201:/home/uli/docker/ngue-app/

#### Static-Ordner kopieren

scp -r static/ uli@192.168.178.201:/home/uli/docker/ngue-app/

