import cv2
import object_socket


s = object_socket.ObjectReceiverSocket('127.0.0.1', 5000, print_when_connecting_to_sender=True, print_when_receiving_object=True)

while True:
    ret, frame = s.recv_object()
    if not ret:
        break

    cv2.imshow('Frame', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

# for i in range(5):
#     a = s.recv()
#
#     print(f'\n--- {i} ---\n')
#     print(a)


















