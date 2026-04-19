#ifndef HM01B0_H
#define HM01B0_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "hardware/i2c.h"
#include "hardware/pio.h"

typedef struct {
    i2c_inst_t *i2c;
    uint sda_pin;
    uint scl_pin;
    uint vsync_pin;
    uint hsync_pin;
    uint pclk_pin;
    uint data_pin_base;
    PIO pio;
    uint pio_sm;
    uint dma_channel;
    uint width;
    uint height;
    uint32_t frame_counter;
} hm01b0_config_t;

void hm01b0_init(hm01b0_config_t *cfg);
void hm01b0_read_frame(hm01b0_config_t *cfg, uint8_t *buffer, size_t size);

#endif // HM01B0_H
