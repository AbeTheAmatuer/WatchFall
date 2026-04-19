#include "hm01b0.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"

static void hm01b0_init_i2c(hm01b0_config_t *cfg) {
    i2c_init(cfg->i2c, 100 * 1000);
    gpio_set_function(cfg->sda_pin, GPIO_FUNC_I2C);
    gpio_set_function(cfg->scl_pin, GPIO_FUNC_I2C);
    gpio_pull_up(cfg->sda_pin);
    gpio_pull_up(cfg->scl_pin);
}

static void hm01b0_init_data_pins(hm01b0_config_t *cfg) {
    gpio_init(cfg->vsync_pin);
    gpio_set_dir(cfg->vsync_pin, GPIO_IN);
    gpio_init(cfg->hsync_pin);
    gpio_set_dir(cfg->hsync_pin, GPIO_IN);
    gpio_init(cfg->pclk_pin);
    gpio_set_dir(cfg->pclk_pin, GPIO_IN);
    for (uint pin = cfg->data_pin_base; pin < cfg->data_pin_base + 8; ++pin) {
        gpio_init(pin);
        gpio_set_dir(pin, GPIO_IN);
    }
}

void hm01b0_init(hm01b0_config_t *cfg) {
    cfg->frame_counter = 0;
    hm01b0_init_i2c(cfg);
    hm01b0_init_data_pins(cfg);
}

void hm01b0_read_frame(hm01b0_config_t *cfg, uint8_t *buffer, size_t size) {
    size_t expected = cfg->width * cfg->height;
    if (size < expected) {
        return;
    }

    // TODO: replace this synthetic test pattern with actual HM01B0 capture logic.
    for (size_t i = 0; i < expected; ++i) {
        buffer[i] = (uint8_t)((i + cfg->frame_counter) & 0xFF);
    }
    cfg->frame_counter++;
    sleep_ms(33);
}
