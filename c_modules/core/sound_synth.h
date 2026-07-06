#ifndef SOUND_SYNTH_H
#define SOUND_SYNTH_H

#include <stdint.h>
#include <stdbool.h>

#define SOUND_SYNTH_MAX_CHANNELS 4

typedef struct {
    uint16_t freq;
    uint8_t wave_type;
    uint8_t volume;
    uint32_t phase;
    uint32_t samples_played;
} sound_synth_channel_t;

void sound_synth_init(int sample_rate);
void sound_synth_set_channel(int ch, uint16_t freq, uint8_t wave_type, uint8_t volume);
void sound_synth_stop_all(void);

// For ESP32 (I2S DMA buffer)
void sound_synth_render_int16(int16_t* buffer, int num_samples);

// For WASM (AudioWorklet output arrays)
void sound_synth_render_float(float* out_l, float* out_r, int num_samples);

// For WASM zero-copy (avoiding malloc in AudioWorklet)
#define SOUND_SYNTH_WASM_RENDER_SIZE 128
float* sound_synth_get_wasm_buf_l(void);
float* sound_synth_get_wasm_buf_r(void);
void sound_synth_render_wasm(void);

#endif // SOUND_SYNTH_H
