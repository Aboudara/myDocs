// ui.cpp
#include <Arduino.h>
#include <lvgl.h>
#include "lvgl_v8_port.h"
#include "esp_panel_board_custom_conf.h"

#include "ui.h"
#include "grafcet.h"
#include "modbus_io.h"

// Image LVGL générée à partir du PNG
extern const lv_img_dsc_t Logo_Oxygen;

// Police plus grande pour icônes / textes
extern const lv_font_t lv_font_montserrat_30;

// =========================
//  UI: objets et données
// =========================
static int      current_page      = 0;   // 0 = accueil, 1 = principale, 2 = reglages
static lv_obj_t *page_accueil    = nullptr;
static lv_obj_t *page_principale = nullptr;
static lv_obj_t *page_reglages   = nullptr;

static lv_obj_t *label_entrees    = nullptr;
static lv_obj_t *label_etape_num  = nullptr;
static lv_obj_t *label_etape_desc = nullptr;
static lv_obj_t *label_timer      = nullptr;
static lv_obj_t *label_val_tempo1 = nullptr;
static lv_obj_t *label_val_tempo2 = nullptr;
static lv_obj_t *slider_tempo1    = nullptr;
static lv_obj_t *slider_tempo2    = nullptr;

// boutons de navigation
static lv_obj_t *btn_home         = nullptr;  // sur page principale
static lv_obj_t *btn_settings     = nullptr;  // sur page principale
static lv_obj_t *btn_home_reg     = nullptr;  // sur page réglages
static lv_obj_t *btn_settings_reg = nullptr;  // sur page réglages

static const char* STEP_NAMES[] = {
    "S0 - Repos", "S10 - Attente stab", "S11 - Tempo 1",
    "S20 - Attente P20", "S21 - Retour", "S30 - Attente stab",
    "S31 - Tempo 2", "S40 - Choix cycle", "S41 - Cycle 1 fin",
    "S42 - Cycle 2 fin", "S50 - Attente P10", "S51 - Retour"
};
static const char* STEP_SHORT_NAMES[] = {
    "S0", "S10", "S11", "S20", "S21", "S30", "S31", "S40", "S41", "S42", "S50", "S51"
};

static lv_color_t get_color_fluo() { return lv_color_hex(0x39FF14); }
static lv_color_t get_color_cyan() { return lv_color_hex(0x34e2d3); }

// =========================
//  Mise à jour style nav
// =========================
static void update_nav_buttons_style() {
    lv_color_t blue = lv_color_hex(0x007BFF);
    lv_color_t grey = lv_color_hex(0x777777);

    if (current_page == 1) { // page principale
        if (btn_home)         lv_obj_set_style_bg_color(btn_home,         blue, 0);
        if (btn_settings)     lv_obj_set_style_bg_color(btn_settings,     grey, 0);
        if (btn_home_reg)     lv_obj_set_style_bg_color(btn_home_reg,     grey, 0);
        if (btn_settings_reg) lv_obj_set_style_bg_color(btn_settings_reg, grey, 0);
    }
    else if (current_page == 2) { // page reglages
        if (btn_home)         lv_obj_set_style_bg_color(btn_home,         grey, 0);
        if (btn_settings)     lv_obj_set_style_bg_color(btn_settings,     blue, 0);
        if (btn_home_reg)     lv_obj_set_style_bg_color(btn_home_reg,     grey, 0);
        if (btn_settings_reg) lv_obj_set_style_bg_color(btn_settings_reg, blue, 0);
    }
    else { // page accueil
        if (btn_home)         lv_obj_set_style_bg_color(btn_home,         grey, 0);
        if (btn_settings)     lv_obj_set_style_bg_color(btn_settings,     grey, 0);
        if (btn_home_reg)     lv_obj_set_style_bg_color(btn_home_reg,     grey, 0);
        if (btn_settings_reg) lv_obj_set_style_bg_color(btn_settings_reg, grey, 0);
    }
}


// =========================
//  Callbacks LVGL
// =========================
static void btn_home_cb(lv_event_t *e) {
    Serial.println("HOME clique");

    // retour vers page principale depuis réglages
    lv_obj_add_flag(page_reglages,    LV_OBJ_FLAG_HIDDEN);
    lv_obj_clear_flag(page_principale,LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(page_accueil,     LV_OBJ_FLAG_HIDDEN);

    current_page = 1;
    grafcet_set_enabled(true);   // reprise GRAFCET
    update_nav_buttons_style();
}

static void btn_settings_cb(lv_event_t *e) {
    Serial.println("REGLAGES clique");

    // sécurité : interdire si GRAFCET pas en S0 (option client)
    if (!grafcet_is_idle()) {
        Serial.println("Refus REGLAGES : GRAFCET en cours");
        return;
    }

    lv_obj_add_flag(page_principale, LV_OBJ_FLAG_HIDDEN);
    lv_obj_clear_flag(page_reglages,  LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(page_accueil,     LV_OBJ_FLAG_HIDDEN);

    current_page = 2;
    grafcet_set_enabled(false);  // pause GRAFCET en réglages
    update_nav_buttons_style();
}

static void slider_tempo1_cb(lv_event_t *e) {
    int32_t val = lv_slider_get_value(slider_tempo1);
    unsigned long T1 = (unsigned long)val * 1000;
    grafcet_set_TEMPO_1(T1);
    lv_label_set_text_fmt(label_val_tempo1, "%d s", (int)val);
}

static void slider_tempo2_cb(lv_event_t *e) {
    int32_t val = lv_slider_get_value(slider_tempo2);
    unsigned long T2 = (unsigned long)val * 1000;
    grafcet_set_TEMPO_2(T2);
    lv_label_set_text_fmt(label_val_tempo2, "%d s", (int)val);
}

static void accueil_btn_cb(lv_event_t *e) {
    Serial.println("ACCUEIL clique");
    lv_obj_add_flag(page_accueil,      LV_OBJ_FLAG_HIDDEN);
    lv_obj_clear_flag(page_principale, LV_OBJ_FLAG_HIDDEN);
    lv_obj_add_flag(page_reglages,     LV_OBJ_FLAG_HIDDEN);

    current_page = 1;
    grafcet_set_enabled(true);   // GRAFCET actif quand page principale
    update_nav_buttons_style();
}

// =========================
//  Création des pages
// =========================
static void create_page_accueil() {
    lv_obj_t *scr = lv_scr_act();

    page_accueil = lv_obj_create(scr);
    lv_obj_set_size(page_accueil, 800, 480);
    lv_obj_align(page_accueil, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_bg_color(page_accueil, get_color_cyan(), 0);
    lv_obj_clear_flag(page_accueil, LV_OBJ_FLAG_SCROLLABLE);

    // Bouton plein écran (zone tactile)
    lv_obj_t *btn = lv_btn_create(page_accueil);
    lv_obj_set_size(btn, 800, 480);
    lv_obj_align(btn, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_border_width(btn, 0, 0);
    lv_obj_set_style_bg_opa(btn, LV_OPA_TRANSP, 0);   // bouton invisible
    lv_obj_add_event_cb(btn, accueil_btn_cb, LV_EVENT_CLICKED, NULL);

    // Image centrée (logo)
    lv_obj_t *img = lv_img_create(btn);
    lv_img_set_src(img, &Logo_Oxygen);
    lv_obj_align(img, LV_ALIGN_CENTER, 0, -40);

    // Texte d’instruction
    lv_obj_t *label2 = lv_label_create(btn);
    lv_label_set_text(label2, "Appuyez pour demarrer");
    lv_obj_align(label2, LV_ALIGN_BOTTOM_MID, 0, -25);
}

static void create_page_principale() {
    lv_obj_t *scr = lv_scr_act();

    page_principale = lv_obj_create(scr);
    lv_obj_set_size(page_principale, 800, 480);
    lv_obj_align(page_principale, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_bg_opa(page_principale, LV_OPA_TRANSP, 0);
    lv_obj_clear_flag(page_principale, LV_OBJ_FLAG_SCROLLABLE);

    // Titre
    lv_obj_t *title = lv_label_create(page_principale);
    lv_label_set_text(title, "DOUCHE A AIR - GRAFCET");
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 20);
    lv_obj_set_style_text_color(title, lv_color_hex(0x0e107b), 0);
    lv_obj_set_style_text_font(title, &lv_font_montserrat_30, 0);

    // Cadre entrées
    lv_obj_t *panel_entrees = lv_obj_create(page_principale);
    lv_obj_set_size(panel_entrees, 350, 200);
    lv_obj_align(panel_entrees, LV_ALIGN_TOP_LEFT, 40, 80);
    lv_obj_set_style_bg_color(panel_entrees, lv_color_hex(0x525551), 0);
    lv_obj_set_style_border_color(panel_entrees, lv_color_hex(0x4ca7c1), 0);
    lv_obj_set_style_border_width(panel_entrees, 4, 0);

    lv_obj_t *label = lv_label_create(panel_entrees);
    lv_label_set_text(label, "ENTREES");
    lv_obj_align(label, LV_ALIGN_TOP_MID, 0, 10);
    lv_obj_set_style_text_color(label, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label, &lv_font_montserrat_30, 0);

    label_entrees = lv_label_create(panel_entrees);
    lv_label_set_text(label_entrees, "P10: OFF\nP20: OFF\nRET: OFF");
    lv_obj_align(label_entrees, LV_ALIGN_TOP_LEFT, 20, 60);
    lv_obj_set_style_text_color(label_entrees, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label_entrees, &lv_font_montserrat_30, 0);

    // Cadre étape
    lv_obj_t *panel_etape = lv_obj_create(page_principale);
    lv_obj_set_size(panel_etape, 380, 200);
    lv_obj_align(panel_etape, LV_ALIGN_TOP_RIGHT, -40, 80);
    lv_obj_set_style_bg_color(panel_etape, lv_color_hex(0x525551), 0);
    lv_obj_set_style_border_color(panel_etape, lv_color_hex(0x4ca7c1), 0);
    lv_obj_set_style_border_width(panel_etape, 4, 0);

    label = lv_label_create(panel_etape);
    lv_label_set_text(label, "ETAPE ACTIVE");
    lv_obj_align(label, LV_ALIGN_TOP_MID, 0, 10);
    lv_obj_set_style_text_color(label, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label, &lv_font_montserrat_30, 0);

    label_etape_num = lv_label_create(panel_etape);
    lv_label_set_text(label_etape_num, "S0");
    lv_obj_align(label_etape_num, LV_ALIGN_CENTER, 0, -20);
    lv_obj_set_style_text_color(label_etape_num, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label_etape_num, &lv_font_montserrat_30, 0);

    label_etape_desc = lv_label_create(panel_etape);
    lv_label_set_text(label_etape_desc, "Repos");
    lv_obj_align(label_etape_desc, LV_ALIGN_CENTER, 0, 30);
    lv_obj_set_style_text_color(label_etape_desc, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label_etape_desc, &lv_font_montserrat_30, 0);

    // Timer
    lv_obj_t *panel_timer = lv_obj_create(page_principale);
    lv_obj_set_size(panel_timer, 400, 70);
    lv_obj_align(panel_timer, LV_ALIGN_CENTER, 0, 120);
    lv_obj_set_style_bg_color(panel_timer, lv_color_hex(0x525551), 0);
    lv_obj_set_style_border_color(panel_timer, lv_color_hex(0x4ca7c1), 0);
    lv_obj_set_style_border_width(panel_timer, 4, 0);

    label_timer = lv_label_create(panel_timer);
    lv_label_set_text(label_timer, "Timer: inactif");
    lv_obj_center(label_timer);
    lv_obj_set_style_text_color(label_timer, lv_color_hex(0x37f205), 0);
    lv_obj_set_style_text_font(label_timer, &lv_font_montserrat_30, 0);

    // Bouton HOME (maison) en bas à gauche
    btn_home = lv_btn_create(page_principale);
    lv_obj_set_size(btn_home, 80, 80);
    lv_obj_align(btn_home, LV_ALIGN_BOTTOM_LEFT, 40, 20);
    lv_obj_add_event_cb(btn_home, btn_home_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *label_home = lv_label_create(btn_home);
    lv_label_set_text(label_home, LV_SYMBOL_HOME);
    lv_obj_center(label_home);
    lv_obj_set_style_text_font(label_home, &lv_font_montserrat_30, 0);

    // Bouton REGLAGES (engrenage) en bas à droite
    btn_settings = lv_btn_create(page_principale);
    lv_obj_set_size(btn_settings, 80, 80);
    lv_obj_align(btn_settings, LV_ALIGN_BOTTOM_RIGHT, -40, 20);
    lv_obj_add_event_cb(btn_settings, btn_settings_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *label_settings = lv_label_create(btn_settings);
    lv_label_set_text(label_settings, LV_SYMBOL_SETTINGS);
    lv_obj_center(label_settings);
    lv_obj_set_style_text_font(label_settings, &lv_font_montserrat_30, 0);
}

static void create_page_reglages() {
    lv_obj_t *scr = lv_scr_act();

    page_reglages = lv_obj_create(scr);
    lv_obj_set_size(page_reglages, 800, 480);
    lv_obj_align(page_reglages, LV_ALIGN_CENTER, 0, 0);
    lv_obj_set_style_bg_color(page_reglages, get_color_cyan(), 0);
    lv_obj_clear_flag(page_reglages, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t *title = lv_label_create(page_reglages);
    lv_label_set_text(title, "REGLAGES");
    lv_obj_align(title, LV_ALIGN_TOP_MID, 0, 20);
    lv_obj_set_style_text_font(title, &lv_font_montserrat_30, 0);

    // Tempo 1
    lv_obj_t *panel1 = lv_obj_create(page_reglages);
    lv_obj_set_size(panel1, 600, 120);
    lv_obj_align(panel1, LV_ALIGN_CENTER, 0, -60);

    lv_obj_t *label = lv_label_create(panel1);
    lv_label_set_text(label, "Temporisation 1");
    lv_obj_align(label, LV_ALIGN_TOP_LEFT, 20, 10);

    slider_tempo1 = lv_slider_create(panel1);
    lv_obj_set_size(slider_tempo1, 400, 20);
    lv_obj_align(slider_tempo1, LV_ALIGN_LEFT_MID, 20, 10);
    lv_slider_set_range(slider_tempo1, 1, 60);
    lv_slider_set_value(slider_tempo1, grafcet_get_TEMPO_1() / 1000, LV_ANIM_OFF);
    lv_obj_add_event_cb(slider_tempo1, slider_tempo1_cb, LV_EVENT_VALUE_CHANGED, NULL);

    label_val_tempo1 = lv_label_create(panel1);
    lv_label_set_text_fmt(label_val_tempo1, "%lu s", grafcet_get_TEMPO_1() / 1000);
    lv_obj_align(label_val_tempo1, LV_ALIGN_RIGHT_MID, -30, 10);

    // Tempo 2
    lv_obj_t *panel2 = lv_obj_create(page_reglages);
    lv_obj_set_size(panel2, 600, 120);
    lv_obj_align(panel2, LV_ALIGN_CENTER, 0, 80);

    label = lv_label_create(panel2);
    lv_label_set_text(label, "Temporisation 2");
    lv_obj_align(label, LV_ALIGN_TOP_LEFT, 20, 10);

    slider_tempo2 = lv_slider_create(panel2);
    lv_obj_set_size(slider_tempo2, 400, 20);
    lv_obj_align(slider_tempo2, LV_ALIGN_LEFT_MID, 20, 10);
    lv_slider_set_range(slider_tempo2, 1, 60);
    lv_slider_set_value(slider_tempo2, grafcet_get_TEMPO_2() / 1000, LV_ANIM_OFF);
    lv_obj_add_event_cb(slider_tempo2, slider_tempo2_cb, LV_EVENT_VALUE_CHANGED, NULL);

    label_val_tempo2 = lv_label_create(panel2);
    lv_label_set_text_fmt(label_val_tempo2, "%lu s", grafcet_get_TEMPO_2() / 1000);
    lv_obj_align(label_val_tempo2, LV_ALIGN_RIGHT_MID, -30, 10);

    // Bouton HOME (maison) en bas à gauche
    btn_home_reg = lv_btn_create(page_reglages);
    lv_obj_set_size(btn_home_reg, 80, 80);
    lv_obj_align(btn_home_reg, LV_ALIGN_BOTTOM_LEFT, 40, 20);
    lv_obj_add_event_cb(btn_home_reg, btn_home_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *label_home_reg = lv_label_create(btn_home_reg);
    lv_label_set_text(label_home_reg, LV_SYMBOL_HOME);
    lv_obj_center(label_home_reg);
    lv_obj_set_style_text_font(label_home_reg, &lv_font_montserrat_30, 0);

    // Bouton REGLAGES (engrenage) en bas à droite
    btn_settings_reg = lv_btn_create(page_reglages);
    lv_obj_set_size(btn_settings_reg, 80, 80);
    lv_obj_align(btn_settings_reg, LV_ALIGN_BOTTOM_RIGHT, -40, 20);
    lv_obj_add_event_cb(btn_settings_reg, btn_settings_cb, LV_EVENT_CLICKED, NULL);

    lv_obj_t *label_settings_reg = lv_label_create(btn_settings_reg);
    lv_label_set_text(label_settings_reg, LV_SYMBOL_SETTINGS);
    lv_obj_center(label_settings_reg);
    lv_obj_set_style_text_font(label_settings_reg, &lv_font_montserrat_30, 0);
}

// =========================
//  API ui.h
// =========================
void ui_init() {
    if (lvgl_port_lock(-1)) {
        create_page_accueil();
        create_page_principale();
        create_page_reglages();

        // Démarrage sur la page accueil
        lv_obj_add_flag(page_principale, LV_OBJ_FLAG_HIDDEN);
        lv_obj_add_flag(page_reglages,   LV_OBJ_FLAG_HIDDEN);
        current_page = 0;
        grafcet_set_enabled(false);   // GRAFCET bloqué sur accueil

        update_nav_buttons_style();
        lvgl_port_unlock();
    }
}

void ui_update() {
    // Timeout inactivité GRAFCET: 10 minutes = 600000 ms
    const unsigned long TIMEOUT_MS = 600000UL;
    unsigned long now = millis();
    unsigned long last_change = grafcet_get_last_change_ms();

    // Si le GRAFCET est activé et n'a pas bougé depuis 10 min, retour accueil
    if (!grafcet_is_idle() && (now - last_change > TIMEOUT_MS)) {
        Serial.println("Inactivite GRAFCET > 10min, retour page ACCUEIL");

        // Masquer la page actuelle
        if (current_page == 1) {
            lv_obj_add_flag(page_principale, LV_OBJ_FLAG_HIDDEN);
        } else if (current_page == 2) {
            lv_obj_add_flag(page_reglages, LV_OBJ_FLAG_HIDDEN);
        }
        lv_obj_clear_flag(page_accueil, LV_OBJ_FLAG_HIDDEN);
        current_page = 0;

        grafcet_set_enabled(false);
        grafcet_init();

        update_nav_buttons_style();
        return;
    }

    // Affichage normal de la page principale
    if (current_page != 1) return;

    if (!lvgl_port_lock(0)) return;

    InputsState in = grafcet_get_last_inputs();
    char buf[64];
    sprintf(buf, "P10: %s\nP20: %s\nRET: %s",
            in.P10 ? "ON" : "OFF",
            in.P20 ? "ON" : "OFF",
            in.RET ? "ON" : "OFF");
    lv_label_set_text(label_entrees, buf);

    Step s = grafcet_get_step();
    lv_label_set_text(label_etape_num, STEP_SHORT_NAMES[s]);
    lv_label_set_text(label_etape_desc, STEP_NAMES[s] + 5);

    if (grafcet_get_timer_active()) {
        unsigned long duree = (s == S11) ? grafcet_get_TEMPO_1()
                                         : grafcet_get_TEMPO_2();
        long reste = (long)(duree - (millis() - grafcet_get_timer_start())) / 1000;
        if (reste < 0) reste = 0;
        lv_label_set_text_fmt(label_timer, "Timer: %lds restantes", reste);
    } else {
        lv_label_set_text(label_timer, "Timer: inactif");
    }

    lvgl_port_unlock();
}
