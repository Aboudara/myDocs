# Liste des adresses de portiques
ADRESSES_PORTIQUES = [0x02 + i for i in range(7)]

# Portiques montés à l'envers
PORTIQUES_INVERSES = {
    0x04: True,
    0x05: True
}

# Port COM par défaut
PORT_COM_DEFAUT = "COM5"

# Baudrate de communication
BAUDRATE = 9600

# Timeout de lecture en secondes
TIMEOUT = 1
