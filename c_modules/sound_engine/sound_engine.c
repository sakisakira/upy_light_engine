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

#define MAX_CHANNELS 4

typedef struct {
    uint16_t freq;
    uint8_t wave_type;
    uint8_t volume;
    uint32_t phase;
} channel_t;

static channel_t channels[MAX_CHANNELS];
static i2s_chan_handle_t tx_chan = NULL;
static TaskHandle_t sound_task_handle = NULL;
static bool engine_running = false;

static void es8311_write_reg(uint8_t reg, uint8_t val) {
    uint8_t data[2] = {reg, val};
    i2c_master_write_to_device(I2C_PORT, ES8311_ADDR, data, 2, 1000 / portTICK_PERIOD_MS);
}

static void sound_task(void *arg) {
    int sample_rate = 44100;
    int16_t sample_buf[512]; // 256 stereo samples (1024 bytes)
    size_t bytes_written;

    while (engine_running) {
        // Check if all channels are silent
        bool all_silent = true;
        for (int c = 0; c < MAX_CHANNELS; c++) {
            if (channels[c].freq > 0 && channels[c].volume > 0) {
                all_silent = false;
                break;
            }
        }

        if (all_silent) {
            // Write silence to prevent under-run noise, but block slightly to avoid spinning
            memset(sample_buf, 0, sizeof(sample_buf));
            i2s_channel_write(tx_chan, sample_buf, sizeof(sample_buf), &bytes_written, portMAX_DELAY);
            continue;
        }

        // Mix all channels
        for (int i = 0; i < 256; i++) {
            int32_t mixed_val = 0;
            for (int c = 0; c < MAX_CHANNELS; c++) {
                if (channels[c].freq > 0 && channels[c].volume > 0) {
                    uint32_t period = sample_rate / channels[c].freq;
                    if (period == 0) continue;
                    uint32_t half_period = period / 2;
                    
                    // wave_type 0 = Square wave
                    int16_t val = ((channels[c].phase % period) < half_period) ? (channels[c].volume * 30) : -(channels[c].volume * 30);
                    mixed_val += val;
                    channels[c].phase++;
                }
            }
            // Clip
            if (mixed_val > 32767) mixed_val = 32767;
            if (mixed_val < -32768) mixed_val = -32768;
            
            sample_buf[i * 2] = (int16_t)mixed_val;     // L
            sample_buf[i * 2 + 1] = (int16_t)mixed_val; // R
        }
        
        esp_err_t err = i2s_channel_write(tx_chan, sample_buf, sizeof(sample_buf), &bytes_written, portMAX_DELAY);
        if (err != ESP_OK) {
            vTaskDelay(10 / portTICK_PERIOD_MS);
        }
    }
    
    // Clear buffer and delete task
    memset(sample_buf, 0, sizeof(sample_buf));
    i2s_channel_write(tx_chan, sample_buf, sizeof(sample_buf), &bytes_written, portMAX_DELAY);
    vTaskDelete(NULL);
}

static mp_obj_t sound_engine_init(void) {
    if (engine_running) {
        return mp_const_none; // Already running
    }

    memset(channels, 0, sizeof(channels));

    // Initialize I2S
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_1, I2S_ROLE_MASTER);
    esp_err_t err = i2s_new_channel(&chan_cfg, &tx_chan, NULL);
    if (err != ESP_OK) mp_raise_msg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to create I2S channel"));

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
    i2s_channel_init_std_mode(tx_chan, &std_cfg);
    i2s_channel_enable(tx_chan);

    // Initialize I2C and ES8311
    i2c_config_t i2c_cfg = {
        .mode = I2C_MODE_MASTER,
        .sda_io_num = I2C_SDA_PIN,
        .scl_io_num = I2C_SCL_PIN,
        .sda_pullup_en = GPIO_PULLUP_ENABLE,
        .scl_pullup_en = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 100000,
    };
    i2c_param_config(I2C_PORT, &i2c_cfg);
    i2c_driver_install(I2C_PORT, i2c_cfg.mode, 0, 0, 0);

    es8311_write_reg(0x00, 0x80); // RESET
    es8311_write_reg(0x01, 0xB5); // MCLK=BCLK
    es8311_write_reg(0x02, 0x18); // MULT_PRE=3
    es8311_write_reg(0x0D, 0x01); // Power up analog
    es8311_write_reg(0x12, 0x00); // Power up DAC
    es8311_write_reg(0x13, 0x10); // Enable HP drive
    es8311_write_reg(0x32, 0xBF); // DAC volume
    es8311_write_reg(0x37, 0x08); // Bypass DAC equalizer

    // Start FreeRTOS task
    engine_running = true;
    xTaskCreate(sound_task, "sound_task", 4096, NULL, 5, &sound_task_handle);

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(sound_engine_init_obj, sound_engine_init);

static mp_obj_t sound_engine_deinit(void) {
    if (!engine_running) return mp_const_none;

    engine_running = false;
    vTaskDelay(100 / portTICK_PERIOD_MS); // Wait for task to finish

    i2s_channel_disable(tx_chan);
    i2s_del_channel(tx_chan);
    i2c_driver_delete(I2C_PORT);
    
    tx_chan = NULL;
    sound_task_handle = NULL;

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(sound_engine_deinit_obj, sound_engine_deinit);

static mp_obj_t sound_engine_set_channel(size_t n_args, const mp_obj_t *args) {
    if (!engine_running) return mp_const_none;

    int ch = mp_obj_get_int(args[0]);
    if (ch < 0 || ch >= MAX_CHANNELS) return mp_const_none;

    channels[ch].freq = mp_obj_get_int(args[1]);
    channels[ch].wave_type = mp_obj_get_int(args[2]);
    channels[ch].volume = mp_obj_get_int(args[3]);
    
    // Reset phase when a new frequency starts
    if (channels[ch].freq == 0) {
        channels[ch].phase = 0;
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(sound_engine_set_channel_obj, 4, 4, sound_engine_set_channel);

static mp_obj_t sound_engine_stop_all(void) {
    for (int i = 0; i < MAX_CHANNELS; i++) {
        channels[i].freq = 0;
        channels[i].volume = 0;
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(sound_engine_stop_all_obj, sound_engine_stop_all);

static const mp_rom_map_elem_t sound_engine_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__sound_engine) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&sound_engine_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit), MP_ROM_PTR(&sound_engine_deinit_obj) },
    { MP_ROM_QSTR(MP_QSTR_set_channel), MP_ROM_PTR(&sound_engine_set_channel_obj) },
    { MP_ROM_QSTR(MP_QSTR_stop_all), MP_ROM_PTR(&sound_engine_stop_all_obj) },
};
static MP_DEFINE_CONST_DICT(sound_engine_module_globals, sound_engine_module_globals_table);

const mp_obj_module_t sound_engine_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&sound_engine_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__sound_engine, sound_engine_user_cmodule);
