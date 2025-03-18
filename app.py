import socket
import threading

import select


def handle_client(client_socket):
    try:
        
        ready_to_read, _, _ = select.select([client_socket], [], [], 1)  
        if ready_to_read:
            
            # mikä 1024? palvelimelle lähetetystä requestista luetaan vain kilotavu
            # oikeissa tapauksissa requestit ovat isompia kuin 1024 tavua,
            # mutta yksinkertaisuuden vuoksi tässä sillä ei ole väliä
            request = client_socket.recv(1024).decode()
            if request:
                print(f"Received request")
                # splitlines() hajoittaa requestin rivinvaihdoista (\n)
                # ['eka rivi', 'toka rivi', 'kolmas rivi']
                lines = request.splitlines()
                # lines[0] on requestin eka rivi
                # se voi näyttää tältä GET / HTTP/1.1
                # split()-metodi hajoittaa rivin välilyönnistä
                # joten 1. tulee metodi, 2. path ja 3. HTTP-protokollaversiolla ei ole väliä tässä esimerkissä
                # koska serveri käyttää vain tcp:tä, eikä upd-protokolla vaihtoehtoa ole
                method, path, _ = lines[0].split()
                headers = {}

                try:

                    # luetaan muut rivit, mutta hypätään eka yli
                    # koska se on jo käsitelty
                    # headerin startlinen jälkeen seuraavat rivit ovat http-protokollan standarissa
                    # headereita
                    for line in lines[1:]:
                        if line:
                            if line.strip() == "":
                                break
                            # hajoitetaan jokainen header avain-arvo -pareihin
                            # esim: Content-Type:application/json

                            key, value = line.split(":", 1)
                            # strip ottaa tyhjät merkit (whitespace) pois
                            # ja jäljelle jää vain teksti
                            headers[key.strip()] = value.strip()
                except ValueError:
                    pass

                # kun requestin osat on käsitelty
                # kutsutaan funktiota, joka käsittelee reqeustin
                # handle_request päättelee metodista, pathista, headerista ja reqeust-bodysta
                # mikä response pitää palauttaa
                response = handle_request(method, path, headers, request)

                # läheteään response clientille takaisin
                client_socket.sendall(response.encode())

    except Exception as e:
        print(f"Error handling client: {e}")
    finally:
        # oikeasti HTTP-palvelimessa
        # kannattaa pitää tcp-yhteys auki
        # useamman mahdollisen http-pyynnön ajan,
        # koska tcp-yhteyden avaaminen vie aikaa
        # mutta tässä serverissä jokainen http-pyyntö avaa ja sulkee tcp-yhteyden
        # (toimii kuin http/1.0)
        client_socket.close()
        print("Client disconnected.")


# IP-osoite, ja porttinumero
# jota tcp-serveri kuuntelee, annetaan parameterina
def start_server(host, port):
    # tämä rivi luo tcp-serverin
    # AF_INET tarkoittaa, että tcp-serveri käyttää IP versio 4. (192.168.1.1)-tyylistä osoitetta
    # SOCK_STREAM tarkoittaa, että serveri käyttää TCP-protokollaa
    # DGRAM käyttäisi UDP:tä (User DataGram Protocol)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # kiinitetään tcp-palvelin haluttuun ip-osoitteeseen ja porttiin
    server_socket.bind((host, port))
    # laitetaan severi päälle
    # 5 on ns. backlog (jolla määritellään pendaavien yhteyksien määrä

    # pendaava yhteys? pendaava yhteys on yhteys, jonka
    # asiakas on, mutta, jota serveri ei  vielä ole hyväksynyt

    server_socket.listen(5)

    print(f"Server listening on {host}:{port}")
    client_socket = None
    try:
        # pyöritetään ikiluuppia, jotta serveri pysyy päällä
        while True:
            # mihin select()iä tarvitaan? tcp-serveri toimii ilman selectiäkin hyvin,
            # mutta sitä ei voisi sammuttaa ilman selectiä,

            ready_to_read, _, _ = select.select([server_socket], [], [], 1)
            # tänne mennään, jos serverille tulee uusia pyyntöjä
            if ready_to_read:
                try:
                    # serveri hyväksyy clientin yhteydenoton
                    client_socket, addr = server_socket.accept()
                    print(f"Client connected from {addr}")

                    # jokaiselle clientille käynnistetään oma thread (säie),
                    # jotta serveri pystyy käsittelemään useamman pyynnön yhtä aikaa

                    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
                    client_thread.start()




                # käsitellään muut mahdolliset virheet
                except Exception as e:
                    print(f"Server error: {e}")
                    break

    except KeyboardInterrupt:
        print("# CTRL+C detected. Shutting down. #")
    finally:
        server_socket.close()
        if client_socket is not None:
            client_socket.close()


def handle_request(method, path, headers, request):
    response_headers = [
        "HTTP/1.1 404 NOT FOUND",
        "Content-Type: text/html"
    ]
    response_body = None
    # jos method on GET, mennään tänne
    if method == "GET":
        # jos path on / tulostetaan HTTP-protokollan mukainen vastaus
        if path == "/":
            response_headers = [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html"
            ]
            response_body = f"<html><body><h1>Hello, World!</h1></body></html>"



    # jos method on POST, tullaan tänne

    elif method == "POST":

        # jos path on /submit
        if path == "/submit":
            # tarkistetaan Content-Type-header
            content_type = headers.get("Content-Type")
            # requestin content-type-headerin arvona application/x-www-form-urlencoded
            # mahdollistaa tekstin lähettämisen formilla serverille
            if content_type == "application/x-www-form-urlencoded":

                try:
                    form_data = {}
                    # \r\n on ns. CRLF (Carriage return line feed)
                    # HTTP-protokollassa tämä tarkoittaa rivinvaihtoa (uutta riviä)
                    # muista, että http-pyyntö (sekä request että response)
                    # on tällainen

                    """
                     GET / HTTP/1.1 (Start Line)
                     Accept: text/html (Headereita voi olla useita)
                     Content-Type: x-www-form-urlencoded
                                       (Blank line, joka erottaa headerit bodysta)
                     first_name=jorma (Body)

                     """
                    # kun reqeust hajoitetaan kahdesta rivinvaihdosta
                    # se tarkoittaa, että [0] indeksissä on start line ja headerit
                    # [1] indeksissä on  body
                    body = request.split("\r\n\r\n", 1)[1]  # Get body
                    for pair in body.split('&'):
                        key, value = pair.split('=')
                        form_data[key] = value
                    response_headers = [
                        "HTTP/1.1 200 OK",
                        "Content-Type: text/html"
                    ]
                    response_body = f"<html><body><h1>Form Submitted! {form_data}</h1></body></html>"



                except Exception:
                    # jos requestissa tapahtuu jokin virhe,
                    # yleensä palvelin lähettää vastauksen http status coden 400, joka tarkoittaa Bad Requestia
                    response_headers = ["HTTP/1.1 400 Bad Request", "Content-Type: text/html"]
                    response_body = "<html><body><h1>Bad Request</h1></body></html>"

            # tänne tullaan, jos path on /submit ja metodi on POST
            # mutta content-type ei ole x-www-form-urlencoded
            if response_body is None:
                response_headers = [
                    "HTTP/1.1 200 OK",
                    "Content-Type: text/html"
                ]
                response_body = "<html><body><h1>Form Submitted!</h1></body></html>"
            # response = "\r\n".join(response_headers) +  "\r\n\r\n" + response_body

    if response_body is None:
        response_body = "<html><body><h1>404 Not Found</h1></body></html>"

    response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body
    return response


if __name__ == "__main__":
    HOST = "127.0.0.1"  # localhost
    PORT = 8080

    start_server(HOST, PORT)
