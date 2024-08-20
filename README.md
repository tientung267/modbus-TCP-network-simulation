# modbus-TCP-network-simulation
Für einen besseren Einblick in die Struktur des Experimentprojekts siehe folgende Grafik
![image](https://github.com/user-attachments/assets/b79ed49f-a95f-4479-b117-0564ba1088bd)

# Einführung: 
Eine zentrale Komponente dieses Projekts ist die pyModbusTCP-Bibliothek in Python. Die Bibliothek stellt Modbus-Client- und Modbus-Server-Objekte zur Verfügung, die das Verhalten eines echten Masters (Client) und Slaves (Server) in einem industriellen System simulieren. Der Modbus-Client kann Anfragen wie "Read Holding Registers" oder "Write Single Holding Register" an den Modbus-Server senden. Der Modbus-Server verwaltet eine "DataBank", die selbstkonfigurierte Daten von Coils, Holding Registers, Input Registers usw. enthält. Basierend auf den Anfragen des Modbus-Clients sendet der Modbus-Server die entsprechenden Daten aus der DataBank zurück. In diesem Experiment werden nur zwei Arten von Anfragen betrachtet: "Read Single Holding Register" und "Write Single Holding Register".

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
  
### Einbettung: Das Einbetten werden in Segment B ausgeführt
### Auslesen des eingebetteten Nachrichts: 
#### Size Modulation: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment C ab. In C wird für jeden ankommende Modbus/TCP Packet das "Length" Feld im mbap-header extrahiert.
#### Inter-Packet-Times: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment A ab. In A wird die Round-Trip-Time für jeden gesendeten Modbus/TCP Paket gerechnet. Da aber die Netzwerkdrosselung im Segment B die Verzögerung um 1 erhört muss es auch beachtet werden, dass nur die Nachkommazahlen ([0.25, 0.5]) als steganografische eingebettete Verzögerung betrachtet werden soll bei Nachrichtempfänger.

## Testumgebung
### Docker Container
Die Modbus-Klient, Modbus-Server und Übergangserver werden jeweils in einem Docker Container ausgeführt, jeder Container repräsentiert eine isolierte Umgebung. Diese Isolation ermöglicht es, Anwendungen und deren Abhängigkeiten unabhängig von der zugrunde liegenden Host-Umgebung und unabhängig von anderen Applikationen laufen zu lassen. Diese Konfiguration ermöglicht eine Segmentierung des Netzwerks wie in der obigen Grafik, darüberhinaus können das Ergebnis des Experiments in anderen Host-Umgebung reproduziert werden. Ich selber habe das Experiment in Window mit **WSL2** (Windows Subsystem for Linux 2) ausführe, meine Container hat daher eine **Linux-basierte Betriebssystemumgebung**. Er interagiert ausschließlich mit dem Linux-Kernel und führt Linux-basierte Anwendungen und Bibliotheken aus.

### Docker Images
Zum Ausführen der Container werden zuerst Anwendungsquellcode in einem Docker Image gebaut. Ein Docker Image ist eine schreibgeschützte Vorlage für den Aufbau eines Docker Containers. Es enthält alles, was notwendig ist, um eine Anwendung auszuführen, einschließlich:
    - Der Anwendungs-Quellcode
    - Bibliotheken und Abhängigkeiten
    - Umgebungsvariablen
    - Konfigurationsdateien
    - System-Tools und -Anwendungen
Alle Images von diesem Experiment werden in einem Repository in Docker-Hub öffentlich zur Verfügung gestellt: 
- Gateway-Serer image (Für Segment B): https://hub.docker.com/repository/docker/tientungnguyen/gateway-server-image/general
- Modbus-Klient image (Für Segment A): https://hub.docker.com/repository/docker/tientungnguyen/modbus-client-image/general
- Modbus-Server image....
### Docker-compose.yml
Der docker compose Datei ermöglicht die Ausführung gleichzeitig alle drei Container in einem gemeinsamen Netzwerk. Die Ports von Applikationen werden jeweils mit einem Container Port zugeordnet.
