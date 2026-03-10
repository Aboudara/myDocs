#include "modbus_io.h"

#define MODBUS_RXD 43
#define MODBUS_TXD 44

static int compteur_erreurs = 0;

static uint16_t calculerCRC16(uint8_t* data, int len) {
    uint16_t crc = 0xFFFF;
    for (int i = 0; i < len; i++) {
        crc ^= data[i];
        for (int j = 0; j < 8; j++) {
            if (crc & 1) crc = (crc >> 1) ^ 0xA001;
            else         crc = crc >> 1;
        }
    }
    return crc;
}

void modbus_init() {
    gpio_reset_pin((gpio_num_t)MODBUS_TXD);
    gpio_reset_pin((gpio_num_t)MODBUS_RXD);

    uart_config_t uart_config = {
        .baud_rate = 9600,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk= UART_SCLK_APB,
    };

    uart_param_config(UART_NUM_1, &uart_config);
    uart_set_pin(UART_NUM_1, MODBUS_TXD, MODBUS_RXD, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(UART_NUM_1, 256, 0, 0, NULL, 0);

    modbus_all_relays_off();
}

static int modbusTransaction(uint8_t* req, int lenReq, uint8_t* rep, int maxLen) {
    uart_flush(UART_NUM_1);
    uart_write_bytes(UART_NUM_1, (const char*)req, lenReq);
    uart_wait_tx_done(UART_NUM_1, 50);
    delay(50);
    int len = uart_read_bytes(UART_NUM_1, rep, maxLen, 50);
    return len;
}

bool modbus_write_relay(RelayChannel canal, bool on) {
    uint8_t req[8] = {0x01, 0x05, 0x00, (uint8_t)canal, on ? 0xFF : 0x00, 0x00, 0x00, 0x00};
    uint16_t crc = calculerCRC16(req, 6);
    req[6] = crc & 0xFF;
    req[7] = (crc >> 8) & 0xFF;

    uint8_t rep[8];
    int len = modbusTransaction(req, 8, rep, 8);
    bool ok = (len >= 8 && rep[0] == 0x01 && rep[1] == 0x05);
    if (!ok) compteur_erreurs++;
    return ok;
}

bool modbus_read_inputs(InputsState &in) {
    uint8_t req[8] = {0x01, 0x02, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00};
    uint16_t crc = calculerCRC16(req, 6);
    req[6] = crc & 0xFF;
    req[7] = (crc >> 8) & 0xFF;

    uint8_t rep[8];
    int len = modbusTransaction(req, 8, rep, 8);

    if (len >= 4 && rep[0] == 0x01 && rep[1] == 0x02) {
        uint8_t etat = rep[3];
        in.P10 = etat & 0x01;
        in.P20 = etat & 0x02;
        in.RET = etat & 0x04;
        return true;
    }
    compteur_erreurs++;
    return false;
}

void modbus_all_relays_off() {
    for (int c = 0; c < 8; c++) {
        modbus_write_relay((RelayChannel)c, false);
        delay(10);
    }
}
