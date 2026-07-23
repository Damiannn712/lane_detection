import cv2
import object_socket

# Initializam conexiunea ca Sender
s = object_socket.ObjectSenderSocket('127.0.0.1', 5000, print_when_awaiting_receiver=True)

# Incarcam videoclipul (folosim numele pe care l-ai corectat anterior)
video = cv2.VideoCapture('Lane Detection Test Video 01.mp4')

while True:
    # Citim fiecare frame din video
    ret, frame = video.read()
    
    # Trimitem tuplul (ret, frame) catre scriptul de procesare
    s.send_object((ret, frame))

    # Daca am ajuns la finalul videoclipului, oprim bucla
    if not ret:
        break

    # Permitem oprirea manuala cu tasta 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video.release()