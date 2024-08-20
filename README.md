# modbus-TCP-network-simulation
Für einen besseren Einblick in die Struktur des Experimentprojekts siehe folgende Grafik
![image](https://github.com/user-attachments/assets/b79ed49f-a95f-4479-b117-0564ba1088bd)

# Einführung: 
Eine zentrale Komponente dieses Projekts ist die pyModbusTCP-Bibliothek in Python. Die Bibliothek stellt Modbus-Client- und Modbus-Server-Objekte zur Verfügung, die das Verhalten eines echten Masters (Client) und Slaves (Server) in einem industriellen System simulieren. Der Modbus-Client kann Anfragen wie „Read Holding Registers“ oder „Write Single Holding Register“ an den Modbus-Server senden. Der Modbus-Server verwaltet eine DataBank, die selbstkonfigurierte Daten von Coils, Holding Registers, Input Registers usw. enthält. Basierend auf den Anfragen des Modbus-Clients sendet der Modbus-Server die entsprechenden Daten aus der DataBank zurück. In diesem Experiment werden nur zwei Arten von Anfragen betrachtet: "Read Single Holding Register" und "Write Single Holding Register".

## Segment A:
In Segment A wird ein Modbus-Client instanziiert. Zur Erfassung des Fingerabdrucks des Modbus/TCP-Kommunikationsverhaltens werden einige eingebaute Funktionen und Klassen des Modbus-Client-Moduls von pyModbusTCP überschrieben, um Logging zu implementieren. Details des Modbus/TCP-Pakets, wie MBAP-Header und PDU-Payload, werden sowohl beim Absenden des Pakets als auch beim Empfang der Antwort protokolliert. Zudem erfolgt eine Anwendungsschicht-Filterung beim Empfang der Antwort vom Server, um die Konsistenz des Modbus/TCP-Pakets zu überprüfen. Es wird geprüft, ob z.B. die Transaktions-ID von Anfrage und Antwort übereinstimmt, ob die Protokoll-ID korrekt ist oder ob der im Header angegebene Wert die zulässige Grenze nicht überschreitet. Auch für die PDU-Payload der Antwort erfolgt eine Filterung.
Der Modbus-Client sendet Anfragen im Abstand von 1 Sekunde an den Modbus-Server. Die Anfragen „Read Single Holding Register“ und „Write Single Holding Register“ werden abwechselnd gesendet.

## Segment B:
Segment B stellt einen Übergang zwischen Modbus-Client und Modbus-Server her. In diesem Segment wird ein Socket instanziiert, der auf Port 500 lauscht. Alle Anfragen vom Modbus-Client kommen zunächst in Segment B an. Drei Mechanismen werden in Segment B implementiert:
- **Zwichenspeicherung:** Wenn ein Wert aus einem Holding Register ausgelesen wird, wird es in einem Zwischenspeicher gespeichert. Bei nächsten "Read Holding Register" Anfragen wird es zuerst im Zwischenspeicher geprüft, ob der Wert vorhanden ist.
- **Netzwerkdrosselung:** In Abstand von 30 Senkunden wird die Sendenrate von Modbus/TCP Paket reduziert. Die Drosselung wird jeweils 10 Sekunde dauert, dabei wird eine Verzögerung von 1 Sekunde für jede Paket im Segment B eingeführt.
- **Protokollnormalisierung:** Angenommen, dass wegen der Konfiguration fängt Transaction id bei Modbus-Klient bei 1, bei Modbus-Server fängt die Trasaktion-ID bei 0, deswegen wird die Transaktion-ID im Header von allen Paketen normalisiert.

### Steganographie: 
Im Segment B wird eine steganografische Nachrichten eingebettet. Es wird 2 Methode implementiert: Interpacket-times und Size-Modulation. Wie diese beiden Methode genau funktionieren, bitte die jeweilige Implementierungen anschauen. Die Idee dabei ist, dass eine Nachrichten String (z.B: "this is a steganography message") in eine bits Reihenfolge konvertiert wird. Dabei ist jeder Character zuerst in seiner Nummer in ASCII Tabelle umgewandet. Diese Nummer wird widerum in eine 7 bits dargestellt (z.B das Charakter 't' wird mit '01110100' dargestellt). da in der ASCII Tabelle 128 Characker existiert, der zu darstellende maximale Nummer ist 127, deswegen kann man alle Character mit 7 bits darstellen. Die ersten 10 bits in der bits Reihenfolge sind sozusagen Header des Nachrichts und stellt die Länge der nachfolgenden bits dar, das bedeutet eine maximale Länge von 1023 bits für den eingebetteten Nachricht.

## Segment C:
In Segment C wird ein Modbus-Server instanziiert. Da wir den Fingerabdruck von Modbus/TCP Kommunikationsverhalten erfassen wollen, werden die eingebaute Funktion und Klasse, die für das Empfangen, Auspacken und Bearbeiten von Modbus/TCP Anfrage zuständig sind, überschrieben, um logging sowie Application-Filterung zu implementieren. Details von Modbus/TCP Paket mbap Header und pdu payload werden einmal beim Empfangen der Anfragen und Absenden des Responses ausgeloggt. Die Application-Layer-Filterung bei dem Empfang von Modbus/TCP request aus Klient prüft die Konsistent des Pakets genauso wie in der Segment A.

## Steganography:
### Inter-Packet-Times: Wie funktioniert es ?
Es gibt zwei Arten von Modbus-Nachrichten, die hier verwendet werden: ReadCoils und WriteSingleCoil.
Eine ReadCoils-Nachricht wird normalerweise pünktlich geschickt. Wenn sie aber um 250 ms verzögert wird, bedeutet das, dass eine 0 übertragen wird.
Eine WriteSingleCoil-Nachricht wird verzögert, um eine 1 zu übertragen.

### Size-Modulation: Wie funtioniert es ?
Eine gerade Länge stellt das Bit 0 dar, 
Eine ungerade Länge stellt das Bit 1 dar.
Wenn die Länge der aktuellen Modbus/TCP Paket mit den zu verschlüsselte Bit nicht übereinstimmt, dann wird die Länge um 1 erhöht, damit die Länge von ungerade zu gerade  oder umgekehrt. Ein "dummy" Byte wird dazu in pdu Payload hinzugefügt.
  
### Einbettung: Das Einbetten werden in Segment B ausgeführt
### Auslesen des eingebetteten Nachrichts: 
#### Size Modulation: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment C ab. In C wird für jeden ankommende Modbus/TCP Packet die Paketlänge Information im Header extrahiert.
#### Inter-Packet-Times: 
Die Methode zielt auf einem Empfänger des Nachrichts in Segment A ab. In A wird die Round Trip Time für jeden gesendeten Modbus/TCP Paket gerechnet. Eine Verzögerung von 0.25ms für eine "Read Single Holding Register" (function code 6) stellt ein Bit 0 dar, eine Verzögerung von 0.25ms für eine "Write Single Holding Register" (function code 3) stellt ein Bit 1 dar. Da aber die Netzwerkdrosselung im Segment B die Verzögerung um 1 erhört muss es auch beachtet werden, dass nur die Nachkommazahlen als steganografische eingebettete Verzögerung betrachtet werden soll bei Nachrichtempfänger.
  
