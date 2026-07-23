import socket

ip = '127.0.0.1'
port = 5001

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind((ip, port))

sock.listen(1)
print('Listening...')

conn, addr = sock.accept()
print('Connected.')

msg = b'Hello!'

# Trimiterea mesajului initial
conn.send(msg)
print(f'Sent message [{msg}].')

# Asteptarea si citirea raspunsului de la receiver
reply = conn.recv(128)
print(f'Received reply [{reply}]')

conn.close()