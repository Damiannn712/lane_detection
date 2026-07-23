import socket
import select
import pickle
import datetime

from typing import *


class ObjectSocketParams:
    OBJECT_HEADER_SIZE_BYTES = 4
    DEFAULT_TIMEOUT_S = 1
    CHUNK_SIZE_BYTES = 1024


class ObjectSenderSocket:
    ip: str
    port: int
    sock: socket.socket
    conn: socket.socket
    print_when_awaiting_receiver: bool
    print_when_sending_object: bool

    def __init__(self, ip: str, port: int,
                 print_when_awaiting_receiver: bool = False,
                 print_when_sending_object: bool = False):
        """Initializeaza un socket capabil sa trimita obiecte Python prin retea.

        Args:
            ip (str): Adresa IP la care va fi legat (bind) socket-ul.
            port (int): Portul de comunicatie pe care va asculta sender-ul.
            print_when_awaiting_receiver (bool, optional): Daca este True, va printa in consola 
                mesaje cand asteapta conectarea receiver-ului. Implicit este False.
            print_when_sending_object (bool, optional): Daca este True, va printa in consola 
                un mesaj cu numarul de octeti la fiecare trimitere a unui obiect. Implicit este False.
        """
        self.ip = ip
        self.port = port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.conn = None

        self.print_when_awaiting_receiver = print_when_awaiting_receiver
        self.print_when_sending_object = print_when_sending_object

        self.await_receiver_conection()

    def await_receiver_conection(self):
        """Asculta si accepta conexiunea de intrare de la un receiver.
        
        Asteapta activ pana cand o conexiune este detectata. Seteaza parametrul
        intern `conn` cu socket-ul clientului.
        """
        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] awaiting receiver connection...')

        self.sock.listen(1)
        self.conn, _ = self.sock.accept()

        if self.print_when_awaiting_receiver:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] receiver connected')

    def close(self):
        """Inchide conexiunea socket curenta cu receiver-ul si reseteaza parametrul conexiunii."""
        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifica stadiul conexiunii cu receiver-ul.

        Returns:
            bool: True daca exista o conexiune activa, False in caz contrar.
        """
        return self.conn is not None

    def send_object(self, obj: Any):
        """Zipeaza/Serializeaza si trimite un obiect Python catre receiver.
        
        Foloseste biblioteca `pickle` pentru a converti obiectul intr-un flux de bytes. 
        Trimite intai un header (dimensiunea obiectului), urmat de datele efective.

        Args:
            obj (Any): Orice obiect de Python care poate fi serializat cu pickle (ex: tuple, liste, numpy arrays).
        """
        data = pickle.dumps(obj)
        data_size = len(data)
        data_size_encoded = data_size.to_bytes(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES, 'little')
        self.conn.sendall(data_size_encoded)
        self.conn.sendall(data)
        if self.print_when_sending_object:
            print(f'[{datetime.datetime.now()}][ObjectSenderSocket/{self.ip}:{self.port}] Sent object of size {data_size} bytes.')



class ObjectReceiverSocket:
    ip: str
    port: int
    conn: socket.socket
    print_when_connecting_to_sender: bool
    print_when_receiving_object: bool

    def __init__(self, ip: str, port: int,
                 print_when_connecting_to_sender: bool = False,
                 print_when_receiving_object: bool = False):
        """Initializeaza un socket capabil sa receptioneze obiecte Python din retea.

        Args:
            ip (str): Adresa IP a sender-ului la care se face conectarea.
            port (int): Portul pe care comunica sender-ul.
            print_when_connecting_to_sender (bool, optional): Daca este True, printeaza starea 
                procesului de conectare. Implicit este False.
            print_when_receiving_object (bool, optional): Daca este True, printeaza dimensiunea 
                obiectului primit la fiecare apel. Implicit este False.
        """
        self.ip = ip
        self.port = port
        self.print_when_connecting_to_sender = print_when_connecting_to_sender
        self.print_when_receiving_object = print_when_receiving_object

        self.connect_to_sender()

    def connect_to_sender(self):
        """Initiaza o conexiune catre adresa si portul sender-ului stabilit."""
        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connecting to sender...')

        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((self.ip, self.port))

        if self.print_when_connecting_to_sender:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] connected to sender')

    def close(self):
        """Inchide si invalideaza conexiunea curenta cu sender-ul."""
        self.conn.close()
        self.conn = None

    def is_connected(self) -> bool:
        """Verifica daca exista o conexiune deschisa cu sender-ul.

        Returns:
            bool: True daca conexiunea este valida, False altfel.
        """
        return self.conn is not None

    def recv_object(self) -> Any:
        """Receptioneaza, decodifica si deserializeaza un obiect Python trimis de sender.

        Actioneaza in doua etape: primeste dimensiunea datelor de intrare, dupa care asteapta
        receptionarea completa a stream-ului de bytes si il transforma inapoi intr-un obiect Python.

        Returns:
            Any: Obiectul Python original transmis de sender (rezultat via `pickle.loads`).
        """
        obj_size_bytes = self._recv_object_size()
        data = self._recv_all(obj_size_bytes)
        obj = pickle.loads(data)
        if self.print_when_receiving_object:
            print(f'[{datetime.datetime.now()}][ObjectReceiverSocket/{self.ip}:{self.port}] Received object of size {obj_size_bytes} bytes.')
        return obj

    def _recv_with_timeout(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> Optional[bytes]:
        """Incearca sa citeasca un anumit numar de bytes pana la expirarea unui timer.

        Args:
            n_bytes (int): Numarul maxim de octeti pe care doreste sa ii citeasca bufferul la acest apel.
            timeout_s (float, optional): Timpul de asteptare in secunde. Implicit preia 
                constanta `DEFAULT_TIMEOUT_S` (1 secunda).

        Returns:
            Optional[bytes]: Un obiect de tip bytes cu datele citite daca bufferul contine informatii, 
                sau None daca timpul a expirat (timeout) inainte de a primi date.
        """
        rlist, _1, _2 = select.select([self.conn], [], [], timeout_s)
        if rlist:
            data = self.conn.recv(n_bytes)
            return data
        else:
            return None  # Only returned on timeout

    def _recv_all(self, n_bytes: int, timeout_s: float = ObjectSocketParams.DEFAULT_TIMEOUT_S) -> bytes:
        """Colecteaza fragmente de date (chunks) succesive pana atinge dimensiunea totala ceruta.

        Aceasta metoda asigura ca pachetele mari, care pot veni fragmentat din retea, 
        sunt complet refacute inainte de procesare.

        Args:
            n_bytes (int): Numarul total absolut de octeti pe care functia trebuie sa ii cumuleze.
            timeout_s (float, optional): Timpul de asteptare per citire (in secunde). 
                Implicit ia valoarea `DEFAULT_TIMEOUT_S`.

        Returns:
            bytes: Fluxul de date complet imbinat, de lungime exacta `n_bytes`.

        Raises:
            socket.error: Daca bufferul nu mai primeste pachete noi un timp mai lung decat timeout-ul
                specificat, va arunca o eroare socket continand informatii despre octetii lipsa.
        """
        data = []
        left_to_recv = n_bytes
        while left_to_recv > 0:
            desired_chunk_size = min(ObjectSocketParams.CHUNK_SIZE_BYTES, left_to_recv)
            chunk = self._recv_with_timeout(desired_chunk_size, timeout_s)
            if chunk is not None:
                data += [chunk]
                left_to_recv -= len(chunk)
            else:  # no more data incoming, timeout
                bytes_received = sum(map(len, data))
                raise socket.error(f'Timeout elapsed without any new data being received. '
                                   f'{bytes_received} / {n_bytes} bytes received.')
        data = b''.join(data)
        return data

    def _recv_object_size(self) -> int:
        """Extrage din buffer primul header care specifica dimensiunea obiectului.

        Returns:
            int: Un numar intreg reprezentand numarul total de octeti pe care 
                il va ocupa obiectul principal.
        """
        data = self._recv_all(ObjectSocketParams.OBJECT_HEADER_SIZE_BYTES)
        obj_size_bytes = int.from_bytes(data, 'little')
        return obj_size_bytes