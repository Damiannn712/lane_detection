import socket

ip = '127.0.0.1'
port = 5001

conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

conn.connect((ip, port))
print('Connected.')

# Primirea mesajului initial de la sender
msg = conn.recv(128)
print(f'Received message [{msg}]')

# Decodarea mesajului (din bytes in string) pentru a-l folosi in text
decoded_msg = msg.decode('utf-8')

# Crearea raspunsului conform cerintei
reply_text = f"Hello! Your message was {decoded_msg}."

# Trimiterea raspunsului inapoi, codificat ca bytes
conn.send(reply_text.encode('utf-8'))

conn.close()