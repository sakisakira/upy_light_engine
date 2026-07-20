#ifndef SOUND_SYNTH_H
#define SOUND_SYNTH_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

#define SOUND_SYNTH_MAX_CHANNELS 4

typedef struct {
    uint16_t freq;
    uint8_t wave_type;
    uint8_t volume;
    uint32_t phase;
    uint32_t samples_played;
} sound_synth_channel_t;

typedef struct {
    uint32_t current_offset;
    uint32_t samples_until_next;
    uint32_t total_samples;
    uint16_t notes_remaining;
    bool is_looping;
    bool overridden;
} sound_synth_ubgm_track_t;

typedef struct {
    uint8_t* data;
    size_t length;
    bool is_playing;
    
    // Per-track state
    sound_synth_ubgm_track_t tracks[SOUND_SYNTH_MAX_CHANNELS];
} sound_synth_ubgm_t;

void sound_synth_init(int sample_rate);
void sound_synth_set_channel(int ch, uint16_t freq, uint8_t wave_type, uint8_t volume);
void sound_synth_set_channel_override(int ch, bool override);
void sound_synth_stop_all(void);

// UBGM Sequencer
bool sound_synth_play_ubgm(const uint8_t* data, size_t length);

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
