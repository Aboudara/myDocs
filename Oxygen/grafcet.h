#pragma once
#include <Arduino.h>
#include "modbus_io.h"

enum Step {
    S0, S10, S11, S20, S21, S30, S31, S40, S41, S42, S50, S51
};

void grafcet_init();
void grafcet_step();
void grafcet_set_enabled(bool en);
void grafcet_set_TEMPO_1(unsigned long t);
void grafcet_set_TEMPO_2(unsigned long t);


// pour l’UI
Step grafcet_get_step();
bool grafcet_get_timer_active();
bool grafcet_is_idle();   // vrai seulement en S0
unsigned long grafcet_get_timer_start();
unsigned long grafcet_get_TEMPO_1();
unsigned long grafcet_get_TEMPO_2();
unsigned long grafcet_get_last_change_ms();
InputsState grafcet_get_last_inputs();
