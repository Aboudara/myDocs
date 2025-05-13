# comms.py

import serial
import time
from config import BAUDRATE, TIMEOUT


def ouvrir_connexion(port):
    return serial.Serial(port, baudrate=BAUDRATE, timeout=TIMEOUT)


def calcul_checksum(trame):
    return sum(trame[1:15]) & 0xFF


def construire_trame_ouverture(adresse, sens):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse, 0x08]
    data = [0x00, 0x00, 0x00] if sens == "entree" else [0x00, 0x03, 0x00]
    trame += data + [0x00] * (8 - len(data))
    trame.append(calcul_checksum(trame))
    return bytes(trame)


def construire_trame_ouverture_permanente(adresse):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse, 0x08, 0x00, 0x04, 0x00]
    trame += [0x00] * 5
    trame.append(calcul_checksum(trame))
    return bytes(trame)


def construire_trame_lecture(adresse):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse, 0x08, 0xFF]
    trame += [0x00] * 7
    trame.append(calcul_checksum(trame))
    return bytes(trame)


def trame_blocage_entree(adresse, mode):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x06, adresse, 0x08,
             mode, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    trame.append(calcul_checksum(trame))
    return bytes(trame)


def trame_reinitialisation(adresse):
    trame = [0xAA, 0x00, 0x01, 0x02, 0x00, adresse, 0x08, 0x01]
    trame += [0x00] * 7
    trame.append(calcul_checksum(trame))
    return bytes(trame)


def envoyer_trame(ser, trame):
    ser.write(trame)
    print("✅ Trame envoyée :", ' '.join(f'{b:02X}' for b in trame))


def lire_infos_entrees_sorties(ser, adresse):
    trame = construire_trame_lecture(adresse)
    ser.reset_input_buffer()
    ser.write(trame)
    time.sleep(1)

    response = bytearray()
    start_time = time.time()
    while len(response) < 16 and time.time() - start_time < 1.0:
        if ser.in_waiting:
            response += ser.read(ser.in_waiting)

    if len(response) == 16 and response[0] == 0xAA:
        entree = (response[11]) | (response[10] << 8) | (response[9] << 16)
        sortie = (response[14]) | (response[13] << 8) | (response[12] << 16)
        return entree, sortie
    return None, None
