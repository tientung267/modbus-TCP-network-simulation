# modbus-TCP-network-simulation
Für einen besseren Einblick in die Struktur des Experimentprojekts siehe folgende Grafik
![image](https://github.com/user-attachments/assets/e8187822-a830-4e97-ac94-1c6c5579363c)

# Einführung: 
Eine zentrale Komponente dieses Projekts ist die pyModbusTCP-Bibliothek in Python. Die Bibliothek stellt Modbus-Client- und Modbus-Server-Objekte zur Verfügung, die eine Modbus-Kommunikationsumgebung simulieren. Im Folgenden sind die Hauptunterschiede und der Zweck der Module aufgeführt:
- **modbusClient:**
  - Stellt eine Python-Implementierung eines Modbus-Clients bereit.
  - Ermöglicht einem Benutzer, Modbus-Nachrichten an einen Modbus-Server zu senden.
  - Der Modbus-Client kann Anfragen wie "Read Holding Registers" oder "Write Single Holding Register" an den Modbus-Server senden. 
  - Kann verwendet werden, um mit realen oder simulierten Modbus-Servern (z.B. Geräten wie PLCs, Sensoren oder Aktoren) zu kommunizieren.

- **modbusServer:**
  - Stellt eine Python-Implementierung eines Modbus-Servers bereit.
  - Kann Anfragen von einem Modbus-Client empfangen und darauf antworten.
  - Dient zur Simulation eines Modbus-fähigen Geräts, wie z.B. eines Sensors oder Aktors.
  - Der Modbus-Server verwaltet eine "DataBank", die selbstkonfigurierte Daten von Coils, Holding Registers, Input Registers usw. enthält. Basierend auf den Anfragen des Modbus-Clients sendet der Modbus-Server die entsprechenden Daten aus der DataBank zurück.

In diesem Experiment werden nur zwei Arten von Anfragen betrachtet: "Read Single Holding Register" und "Write Single Holding Register".

## Segment A:
In Segment A wird ein Modbus-Client instanziiert. Zur Erfassung des Fingerabdrucks des Modbus/TCP-Kommunikationsverhaltens werden einige eingebaute Funktionen und Klassen des Modbus-Client-Moduls von pyModbusTCP überschrieben, um Logging zu implementieren. Details des Modbus/TCP-Pakets, wie MBAP-Header und PDU-Payload, werden sowohl beim Absenden des Pakets als auch beim Empfang der Antwort ausgeloggt. Zudem erfolgt eine Anwendungsschicht-Filterung beim Empfang der Antwort vom Server, um die Konsistenz des Modbus/TCP-Pakets zu überprüfen. Es wird geprüft, ob z.B. die Transaktions-ID von Anfrage und Antwort übereinstimmt, ob die Protokoll-ID korrekt ist oder ob der im Header angegebene Wert die zulässige Grenze nicht überschreitet. Auch für die PDU-Payload der Antwort erfolgt eine Filterung.
Der Modbus-Client sendet Anfragen im Abstand von 1 Sekunde an den Modbus-Server. Die Anfragen "Read Single Holding Register" und "Write Single Holding Register" werden abwechselnd gesendet.

## Segment B:
Segment B stellt einen Übergang zwischen Modbus-Client und Modbus-Server dar. In diesem Segment wird ein Socket instanziiert, der auf Port 500 lauscht. Alle Anfragen vom Modbus-Client kommen zunächst in Segment B an. Drei Mechanismen werden in Segment B implementiert:
- **Zwichenspeicherung:** Wenn ein Wert aus einem Holding Register ausgelesen wird, wird dieser in einem Zwischenspeicher gespeichert. Bei zukünftigen „Read Holding Register“-Anfragen wird zunächst im Zwischenspeicher geprüft, ob der Wert bereits vorhanden ist. Wenn ja, wird der Wert über Modbus/TCP Paket zurück zu Klient gesendet.
- **Netzwerkdrosselung:** Alle 30 Sekunden wird die Senderate der Modbus/TCP-Pakete reduziert. Die Drosselung dauert jeweils 10 Sekunden und es wird eine Verzögerung von 1 Sekunde für jedes Paket in Segment B eingeführt.
- **Protokollnormalisierung:** Angenommen, dass wegen der maschinenspezifischen Konfiguration beginnt die Transaktion-ID beim Modbus-Klient bei 1 und beim Modbus-Server bei 0. Deswegen muss die Transaktion-ID im Header aller Modbus/TCP Paketen normalisiert werden.

### Steganographie: 
Im Segment B wird eine steganografische Nachrichten eingebettet. Zwei Methoden werden implementiert: Interpacket-Times und Size-Modulation. Details zu diesen Methoden sind in den jeweiligen Implementierungen zu finden. Die Idee ist, dass eine Nachricht (z.B. "this is a steganography message") in eine Bit-Sequenz umgewandelt wird. Jeder Charakter wird zuerst in seine ASCII-Dezimalzahl konvertiert und dann in 7 Bit dargestellt (z.B das Charakter 't' wird mit '01110100' dargestellt). Weil in der ASCII Tabelle 128 Characker existiert, alle Charakter werden mit Dezimalzahl von 0 bis 127 dargestellt, dadurch können alle Character mit 7 bits verschlüsselt werden. Die ersten 10 Bits in der Bit-Sequenz stellen den Header der Nachricht dar und geben die Anzahl der folgenden Bits an, was eine maximale Länge von 1023 Bits für die eingebettete Nachricht ermöglicht.

## Segment C:
In Segment C wird ein Modbus-Server instanziiert. Zur Erfassung des Fingerabdrucks des Modbus/TCP-Kommunikationsverhaltens werden die eingebauten Funktionen und Klassen, die für das Empfangen, Auspacken und Bearbeiten von Modbus/TCP-Anfragen zuständig sind, überschrieben, um Logging sowie Anwendungsschicht-Filterung zu implementieren. Details des Modbus/TCP-Pakets, wie MBAP-Header und PDU-Payload, werden beim Empfangen der Anfragen und beim Absenden der Antworten ausgeloggt. Die Anwendungsschicht-Filterung beim Empfang von Modbus/TCP-Anfragen vom Client prüft die Konsistenz des Pakets ähnlich wie in Segment A.

## Steganography:
### Inter-Packet-Times: 
Wie funktioniert es ?
Es gibt zwei Arten von Modbus-Nachrichten, die hier verwendet werden: "Read single Holding Register" und "Write single Holding Register".
Wenn der Round-Trip-Time einer "Read single Holding Register"-Nachricht um 250 ms verzögert wird, bedeutet das, dass eine 0 übertragen wird.
Wenn der Round-Trip-Time einer "Write single Holding Register"-Nachricht um 250 ms verzögert wird, bedeutet das, dass eine 0 übertragen wird.

### Size-Modulation: 
Wie funtioniert es ?
Die "Length" Feld im mbap-header eines Modbus/TCP Pakets wird verwendet, um bits zu verschlüsselt
Eine gerade Länge stellt das Bit 0 dar, 
Eine ungerade Länge stellt das Bit 1 dar.
Wenn die Länge der aktuellen Modbus/TCP Paket mit den zu verschlüsselte Bit nicht übereinstimmt, wird die Länge um 1 erhöht, um von gerade auf ungerade oder umgekehrt zu wechseln. Ein "dummy"-Byte wird dazu in pdu Payload hinzugefügt.

### Methodeanwendung:
Zur Anwendung einer der beiden Methode in dem Experiment kann man die Umgebungsvariable in `docker-compose.yml` setzen (`APPLY_INTER_PACKET_TIMES` in client und gateway containers für t1 oder `APPLY_SIZE_MODULATION` in server und gateway containers für s1 mit einem beliebigen Wert). Für Beispiel siehe `docker-compose.yml`. Bei Default wird inter-packet-times method angewendet (`APPLY_INTER_PACKET_TIMES` wurde gesetzt)
  
### Einbettung: Das Einbetten werden in Segment B ausgeführt
### Auslesen des eingebetteten Nachrichts: 
#### Size Modulation: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment C ab. In C wird für jeden ankommende Modbus/TCP Packet das "Length" Feld im mbap-header extrahiert.
#### Inter-Packet-Times: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment A ab. In A wird die Round-Trip-Time für jeden gesendeten Modbus/TCP Paket gerechnet. Da aber die Netzwerkdrosselung im Segment B die Verzögerung um 1 erhört muss es auch beachtet werden, um steganografische eingebettete Verzögerung zu rechnen, muss die Netzwerkdrosselungsverzögerung abgezogen werden.

## Testumgebung
### Docker Container
Der Modbus-Klient, der Modbus-Server und der Übergangserver werden jeweils in einem Docker-Container ausgeführt. Jeder Container stellt eine isolierte Umgebung dar. Diese Isolation ermöglicht es, Anwendungen und deren Abhängigkeiten unabhängig von der zugrunde liegenden Host-Umgebung und von anderen Applikationen laufen zu lassen. Diese Konfiguration erlaubt eine Segmentierung des Netzwerks, wie in der obigen Grafik dargestellt. Darüber hinaus können die Ergebnisse des Experiments in anderen Host-Umgebungen reproduziert werden. Ich habe das Experiment unter Windows mit **WSL2** (Windows Subsystem for Linux 2) durchgeführt, weshalb meine Container eine **Linux-basierte Betriebssystemumgebung** haben. Sie interagieren ausschließlich mit dem Linux-Kernel und führen Linux-basierte Anwendungen und Bibliotheken aus.

### Requirements
- **Linux:** Docker Engine, Docker CLI, Docker Compose. In Linux sind  Docker Engine und Docker CLI standardmäßig schon installiert.
- **Windows:** Ich habe Docker Desktop verwendet, das schon alle oben 3 Komponenten bereits enthält. Außerdem bietet Docker Desktop GUI, um  Container zu verwalten, Images zu anzeigen, Netzwerke zu überwachen. 

### Docker Images
Zum Ausführen der Container wird zunächst der Anwendungsquellcode in ein Docker-Image gebaut. Ein Docker-Image ist eine schreibgeschützte Vorlage für den Aufbau eines Docker-Containers. Es enthält alles, was notwendig ist, um eine Anwendung auszuführen, einschließlich:
- Der Anwendungsquellcode
- Bibliotheken und Abhängigkeiten
- Umgebungsvariablen
- Konfigurationsdateien
- System-Tools und -Anwendungen
    
Alle Images dieses Experiments werden in einem Repository auf Docker Hub öffentlich zur Verfügung gestellt:
- Gateway-Serer image (Für Segment B): https://hub.docker.com/repository/docker/tientungnguyen/gateway-server-image/general
- Modbus-Klient image (Für Segment A): https://hub.docker.com/repository/docker/tientungnguyen/modbus-client-image/general
- Modbus-Server image (Für Segment C): https://hub.docker.com/repository/docker/tientungnguyen/modbus-server-image/general

### Docker-compose.yml
Die Datei `docker-compose.yml` ermöglicht das gleichzeitige Ausführen aller drei Container in einem gemeinsamen Netzwerk. Die Ports der Applikationen werden jeweils einem Container-Port zugeordnet. Der Modbus-Klient lauscht auf Port 3000, der Gateway-Server auf Port 500, und der Modbus-Server auf Port 502. Die drei Containers kommunizieren miteinander über Containerports und mit Containernamen.

### Logdatei speichern
In der `docker-compose.yml` werden die `stdout` und `stderr` der Container in `.log`-Dateien umgeleitet. Durch die Verwendung von Docker-Volumes können die Logdateien dauerhaft gespeichert werden:
- Unter Windows mit WSL2 werden die Logdateien unter \\wsl.localhost\docker-desktop-data\data\docker\volumes\modbus-tcp-network-simulation_modbus-network-data\_data gespeichert.
- Unter Windows mit WSL2 werden die Logdateien unter /var/lib/docker/volumes/modbus-tcp-network-simulation_modbus-network-data/_data gespeichert.

# Ausführung des Experiments:
- **Mit Docker Compose**: Da alle benötigten Komponenten eines Segments in einem Image gebündelt wurden, kann man diese in einer `docker-compose.yml` Datei definieren. Docker Compose startet daraufhin alle Container in einem isolierten Netzwerk.
  - Zum Starten: docker compose up
  - Zum Beenden: docker compose down
- **Mit `Dockerfile`**: Für jedes Segment ist ein eigenes Dockerfile definiert, mit dem ein Image gebaut und dann als Container ausgeführt werden kann.
  - Reihenfolge: Zuerst muss der Server gestartet werden, gefolgt vom Gateway-Server und schließlich dem Client.
  - Alle Container müssen in einem gemeinsamen Netzwerk laufen, daher sollte ein Docker-Netzwerk erstellt werden.
- **Ohne Docker**: Das Experiment kann auch ohne Docker ausgeführt werden. In diesem Fall haben alle Segmente standardmäßig den Hostnamen localhost. In jedem Segment gibt es eine Startdatei (`StartServer`, `StartGatewayServer` und `StartClient`), um die jeweiligen Segmente manuell zu starten.
