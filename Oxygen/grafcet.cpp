// grafcet.cpp
#include <Arduino.h>
#include "grafcet.h"
#include "modbus_io.h"


// =========================
//  Etat interne GRAFCET
// =========================
static Step current_step  = S0;
static Step previous_step = S0;

static unsigned long TEMPO_1 = 10000;   // 10 s
static unsigned long TEMPO_2 = 10000;   // 10 s
static unsigned long timer_start = 0;
static bool          timer_actif = false;

// RET piloté par l'IHM (toggle sur page réglages)
static bool RET_ihm = false;

static InputsState last_inputs = {false, false, false};
static bool grafcet_enabled = false;          // bloqué par défaut (page accueil)
static unsigned long last_step_change_ms = 0; // dernière évolution d'étape


// =========================
//  API interne
// =========================
static void start_timer() {
    timer_start = millis();
    timer_actif = true;
}

static bool elapsed(unsigned long duree) {
    if (!timer_actif) return false;
    if (millis() - timer_start >= duree) {
        timer_actif = false;
        return true;
    }
    return false;
}

static void apply_outputs_for_step(Step step) {
    bool VV=0, VJ=0, VR=0, M=0, ECL=0, V1=0, V2=0;
    switch(step) {
        case S0:  VV=1; break;

        case S10:
            VJ=1; ECL=1; V2=1;
            break;

        case S11:
            VR=1; M=1; ECL=1; V1=1; V2=1;
            break;

        case S20:
        case S21:
        case S42:
            VJ=1; ECL=1; V1=1;
            break;

        case S30:
            VJ=1; ECL=1; V1=1;
            break;

        case S31:
            VR=1; M=1; ECL=1; V1=1; V2=1;
            break;

        case S40:
            VJ=1; ECL=1;
            break;

        case S41:
        case S50:
        case S51:
            VJ=1; ECL=1; V2=1;
            break;
    }

    modbus_write_relay(REL_VV, VV);
    modbus_write_relay(REL_VJ, VJ);
    modbus_write_relay(REL_VR, VR);
    modbus_write_relay(REL_M,  M);
    modbus_write_relay(REL_ECL,ECL);
    modbus_write_relay(REL_V1, V1);
    modbus_write_relay(REL_V2, V2);
}


// =========================
//  Implémentation API grafcet.h
// =========================
void grafcet_init() {
    current_step  = S0;
    previous_step = S0;
    timer_actif   = false;
    last_inputs   = {false,false,false};
    last_step_change_ms = millis();

    modbus_all_relays_off();
    // S0 : VV = ON
    modbus_write_relay(REL_VV, true);
}

void grafcet_set_enabled(bool en) {
    grafcet_enabled = en;
}

// nouveau: pilotage RET par l'IHM
void grafcet_set_RET_ihm(bool v) {
    RET_ihm = v;
}

void grafcet_step() {
    if (!grafcet_enabled) return;   // ne rien faire si désactivé

    InputsState in;
    if (!modbus_read_inputs(in)) return;

    // Combinaison RET physique + RET IHM (OU logique)
    in.RET = in.RET || RET_ihm;

    last_inputs = in;
    previous_step = current_step;

    switch(current_step) {
        case S0:
            if (in.P10)      current_step = S10;
            else if (in.P20) current_step = S30;
            break;

        case S10:
            if (!in.P10 && !in.P20) {
                current_step = S11;
                start_timer();
            }
            break;

        case S11:
            if (elapsed(TEMPO_1))
                current_step = in.RET ? S40 : S20;
            break;

        case S20:
            if (in.P20) current_step = S21;
            break;

        case S21:
            if (!in.P10 && !in.P20) current_step = S0;
            break;

        case S40:
            if (in.P10)      current_step = S41;
            else if (in.P20) current_step = S42;
            break;

        case S41:
        case S42:
            if (!in.P10 && !in.P20) current_step = S0;
            break;

        case S30:
            if (!in.P10 && !in.P20) {
                current_step = S31;
                start_timer();
            }
            break;

        case S31:
            if (elapsed(TEMPO_2))
                current_step = in.RET ? S40 : S50;
            break;

        case S50:
            if (in.P10) current_step = S51;
            break;

        case S51:
            if (!in.P10 && !in.P20) current_step = S0;
            break;

        default:
            current_step = S0;
            break;
    }

    if (current_step != previous_step) {
        last_step_change_ms = millis();
        apply_outputs_for_step(current_step);
    }
}


// Getters pour l’UI
Step grafcet_get_step() { return current_step; }

bool grafcet_get_timer_active() { return timer_actif; }

unsigned long grafcet_get_timer_start() { return timer_start; }

unsigned long grafcet_get_TEMPO_1() { return TEMPO_1; }

unsigned long grafcet_get_TEMPO_2() { return TEMPO_2; }

InputsState grafcet_get_last_inputs() { return last_inputs; }

void grafcet_set_TEMPO_1(unsigned long t) { TEMPO_1 = t; }

void grafcet_set_TEMPO_2(unsigned long t) { TEMPO_2 = t; }

bool grafcet_is_idle() {
    return (current_step == S0);
}

unsigned long grafcet_get_last_change_ms() {
    return last_step_change_ms;
}
