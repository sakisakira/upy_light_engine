#include "py/runtime.h"
#include "py/obj.h"
#include "py/mpprint.h"
#include "driver/i2s_std.h"
#include "driver/i2c.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

#define I2S_BCLK_PIN 41
#define I2S_WS_PIN   43
#define I2S_DOUT_PIN 42
#define I2C_SCL_PIN  9
#define I2C_SDA_PIN  8
#define ES8311_ADDR  0x18
#define I2C_PORT     I2C_NUM_1

static i2s_chan_handle_t tx_chan;

static void es8311_write_reg(uint8_t reg, uint8_t val) {
    uint8_t data[2] = {reg, val};
    esp_err_t err = i2c_master_write_to_device(I2C_PORT, ES8311_ADDR, data, 2, 1000 / portTICK_PERIOD_MS);
    if (err != ESP_OK) {
        mp_printf(&mp_plat_print, "ES8311 I2C Err: reg=0x%02x, err=%d\n", reg, err);
    }
}

static mp_obj_t sound_engine_test_sound(void) {
    mp_printf(&mp_plat_print, "Starting C module sound test...\n");

    // 1. AMP is controlled via ES8311 internally, no GPIO to toggle

    // 2. Initialize I2S
    esp_err_t err;
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
    err = i2s_new_channel(&chan_cfg, &tx_chan, NULL);
    if (err != ESP_OK) mp_printf(&mp_plat_print, "I2S new_channel err: %d\n", err);

    i2s_std_config_t std_cfg = {
        .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(44100),
        .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_STEREO),
        .gpio_cfg = {
            .mclk = I2S_GPIO_UNUSED,
            .bclk = I2S_BCLK_PIN,
            .ws = I2S_WS_PIN,
            .dout = I2S_DOUT_PIN,
            .din = I2S_GPIO_UNUSED,
            .invert_flags = {
                .mclk_inv = false,
                .bclk_inv = false,
                .ws_inv = false,
            },
        },
    };
    err = i2s_channel_init_std_mode(tx_chan, &std_cfg);
    if (err != ESP_OK) mp_printf(&mp_plat_print, "I2S init_std_mode err: %d\n", err);
    err = i2s_channel_enable(tx_chan);
    if (err != ESP_OK) mp_printf(&mp_plat_print, "I2S enable err: %d\n", err);

    // 3. Initialize I2C
    i2c_config_t i2c_cfg = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_SDA_PIN,
        .scl_io_num = I2C_SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 100000,
    };
    i2c_param_config(I2C_PORT, &i2c_cfg);
    err = i2c_driver_install(I2C_PORT, i2c_cfg.mode, 0, 0, 0);
    if (err != ESP_OK) mp_printf(&mp_plat_print, "I2C driver install err: %d\n", err);

    // 4. Configure ES8311
    // ES8311 Init array from M5Unified
    es8311_write_reg(0x00, 0x80); // RESET/ CSM POWER ON
    es8311_write_reg(0x01, 0xB5); // CLOCK_MANAGER/ MCLK=BCLK
    es8311_write_reg(0x02, 0x18); // CLOCK_MANAGER/ MULT_PRE=3
    es8311_write_reg(0x0D, 0x01); // SYSTEM/ Power up analog circuitry
    es8311_write_reg(0x12, 0x00); // SYSTEM/ power-up DAC
    es8311_write_reg(0x13, 0x10); // SYSTEM/ Enable output to HP drive
    es8311_write_reg(0x32, 0xBF); // DAC volume
    es8311_write_reg(0x37, 0x08); // Bypass DAC equalizer
    
    mp_printf(&mp_plat_print, "ES8311 initialized.\n");

    // 5. Generate and play a square wave for 1 second
    int freq = 440;
    int sample_rate = 44100;
    int duration_ms = 1000;
    int num_samples = (sample_rate * duration_ms) / 1000;
    int period = sample_rate / freq;
    
    int phase = 0;
    size_t bytes_written;
    int16_t sample_buf[512]; // 256 stereo samples

    for (int i = 0; i < num_samples; ) {
        int to_write = (num_samples - i > 256) ? 256 : (num_samples - i);
        for (int j = 0; j < to_write; j++) {
            int16_t val = ((phase % period) < (period / 2)) ? 4000 : -4000;
            sample_buf[j * 2]     = val; // L
            sample_buf[j * 2 + 1] = val; // R
            phase++;
        }
        esp_err_t err = i2s_channel_write(tx_chan, sample_buf, to_write * 4, &bytes_written, portMAX_DELAY);
        if (err != ESP_OK) {
            mp_printf(&mp_plat_print, "i2s_channel_write failed: %d\n", err);
            break;
        }
        i += to_write;
    }

    // Stop and cleanup
    memset(sample_buf, 0, sizeof(sample_buf));
    i2s_channel_write(tx_chan, sample_buf, sizeof(sample_buf), &bytes_written, portMAX_DELAY);
    
    i2s_channel_disable(tx_chan);
    i2s_del_channel(tx_chan);
    i2c_driver_delete(I2C_PORT);
    
    mp_printf(&mp_plat_print, "Test finished.\n");
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(sound_engine_test_sound_obj, sound_engine_test_sound);

static const mp_rom_map_elem_t sound_engine_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__sound_engine) },
    { MP_ROM_QSTR(MP_QSTR_test_sound), MP_ROM_PTR(&sound_engine_test_sound_obj) },
};
static MP_DEFINE_CONST_DICT(sound_engine_module_globals, sound_engine_module_globals_table);

const mp_obj_module_t sound_engine_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&sound_engine_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__sound_engine, sound_engine_user_cmodule);
