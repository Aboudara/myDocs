#pragma once
#include <Arduino.h>
#include <driver/uart.h>
#include <driver/gpio.h>

enum RelayChannel {
    REL_V1   = 0,
    REL_V2   = 1,
    REL_M    = 2,
    REL_ECL  = 3,
    REL_VV   = 4,
    REL_VJ   = 5,
    REL_VR   = 6,
    REL_FREE = 7
};

struct InputsState {
    bool P10;
    bool P20;
    bool RET;
};

void modbus_init();
bool modbus_read_inputs(InputsState &in);
bool modbus_write_relay(RelayChannel ch, bool on);
void modbus_all_relays_off();
