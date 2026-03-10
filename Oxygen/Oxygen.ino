#include <Arduino.h>
#include <esp_display_panel.hpp>
#include <lvgl.h>
#include "lvgl_v8_port.h"
#include "esp_panel_board_custom_conf.h"

#include "modbus_io.h"
#include "grafcet.h"
#include "ui.h"

using namespace esp_panel::drivers;
using namespace esp_panel::board;

Board *board = nullptr;

void setup() {
    Serial.begin(115200);
    Serial.println("=== OXYGEN GRAFCET - BASE FB + ACCUEIL ===");

    modbus_init();          // UART + relais OFF
    grafcet_init();         // init états GRAFCET

    board = new Board();
    board->init();
    board->begin();
    lvgl_port_init(board->getLCD(), board->getTouch());

    ui_init();              // crée accueil + principale + réglages
}

void loop() {
    static unsigned long lastLogic = 0;
    static unsigned long lastUI    = 0;

    if (millis() - lastLogic > 200) {
        grafcet_step();      // plus de current_page ici
        lastLogic = millis();
    }

    if (millis() - lastUI > 200) {
        ui_update();         // ui_update sait déjà s'il doit afficher ou pas
        lastUI = millis();
    }

    delay(10);
}


