import socket

def send_broadcast():
    print("📡 Outbound jiggler pipeline signal transmitting...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = b"GWICHIN_PERSON_TALKING_ACTOR:99733_SHIH:0.8900_SEAL:NAN_NIUK_KWA_DHIDLII"
    sock.sendto(message, ("127.0.0.1", 9999))
    sock.close()

if __name__ == "__main__":
    send_broadcast()
