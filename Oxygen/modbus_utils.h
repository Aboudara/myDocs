// modbus_utils.h
#ifndef MODBUS_UTILS_H
#define MODBUS_UTILS_H

#include <Arduino.h>
#include <driver/uart.h>
#include <driver/gpio.h>

// Initialisation UART
void initUART();

// Transactions Modbus
int modbusTransaction(uint8_t* req, int lenReq, uint8_t* rep, int maxLen);
uint16_t calculerCRC16(uint8_t* data, int len);
bool writeRelay(int canal, bool on);
bool readAllInputs(bool &P10, bool &P20, bool &RET);

#endif