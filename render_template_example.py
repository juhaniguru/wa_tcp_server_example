import socket
import threading

import select

import template_engine


def render(_template):
    with open(_template, 'r', encoding='utf-8') as f:
        return f.read()


def handle_client(client_socket):
    try:
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


def handle_request(method, path, headers, request):
    response_headers = [
        "HTTP/1.1 404 NOT FOUND",
        "Content-Type: text/html"
    ]
    response = None
    # jos method on GET, mennään tänne
    if method == "GET":

        # jos path on / tulostetaan HTTP-protokollan mukainen vastaus
        # TEHTÄVÄ 1: KORJAA KOODI NIIN, ETTÄ KYSELYSTÄ EI TULE VIRHETTÄ,
        # JA users_list.html-sivun lista näkyy selainikkunassa
        if path == "/users":
            response_headers = [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html; charset=utf-8",

            ]
            response_body = f"{render('./templates/users_list.html')}"
            response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body
        elif path == "/posts":
            response_headers = [
                "HTTP/1.1 200 OK",
                "Content-Type: text/html; charset=utf-8",

            ]
            response_body = f"{render('./templates/posts.html')}"
            t = template_engine.render_simple_template(response_body, {'items': ['Post 1', 'Post 2']})

            response = "\r\n".join(response_headers) + "\r\n\r\n" + t

    if response is None:
        response_body = f"<html><body>Page not re</body></html>"
        response = "\r\n".join(response_headers) + "\r\n\r\n" + response_body

    return response


if __name__ == "__main__":
    HOST = "127.0.0.1"  # localhost
    PORT = 8082

    start_server(HOST, PORT)
