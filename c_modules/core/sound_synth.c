#include "sound_synth.h"
#include <string.h>

static sound_synth_channel_t channels[SOUND_SYNTH_MAX_CHANNELS];
static int current_sample_rate = 44100;
static uint32_t decay_samples = 22050; // 0.5 seconds at 44100Hz

// LCG PRNG
static uint32_t _random_seed = 12345;
static uint32_t _next_random() {
    _random_seed = _random_seed * 1664525 + 1013904223;
    return _random_seed;
}

void sound_synth_init(int sample_rate) {
    current_sample_rate = sample_rate;
    decay_samples = sample_rate / 2; // 0.5s decay
    memset(channels, 0, sizeof(channels));
}

void sound_synth_set_channel(int ch, uint16_t freq, uint8_t wave_type, uint8_t volume) {
    if (ch < 0 || ch >= SOUND_SYNTH_MAX_CHANNELS) return;
    
    channels[ch].freq = freq;
    channels[ch].wave_type = wave_type;
    channels[ch].volume = volume;
    
    if (freq > 0) {
        channels[ch].phase = 0;
        channels[ch].samples_played = 0;
    }
}

void sound_synth_stop_all(void) {
    for (int i = 0; i < SOUND_SYNTH_MAX_CHANNELS; i++) {
        channels[i].freq = 0;
        channels[i].volume = 0;
    }
}

// Core synthesis calculation for a single sample
static int32_t sound_synth_mix_sample(void) {
    int32_t mixed_val = 0;
    
    for (int c = 0; c < SOUND_SYNTH_MAX_CHANNELS; c++) {
        if (channels[c].freq > 0 && channels[c].volume > 0 && channels[c].samples_played < decay_samples) {
            uint32_t period = current_sample_rate / channels[c].freq;
            if (period == 0) continue;
            
            // Linear decay
            float decay_factor = 1.0f - ((float)channels[c].samples_played / (float)decay_samples);
            int32_t current_vol = (int32_t)(channels[c].volume * decay_factor * 30);
            
            uint32_t pos = channels[c].phase % period;
            int16_t val = 0;
            
            if (channels[c].wave_type == 0) { // Square
                uint32_t half_period = period / 2;
                val = (pos < half_period) ? current_vol : -current_vol;
            } else if (channels[c].wave_type == 1) { // Sawtooth
                val = (int16_t)(((pos * current_vol * 2) / period) - current_vol);
            } else if (channels[c].wave_type == 2) { // Triangle
                uint32_t half_period = period / 2;
                if (half_period == 0) half_period = 1; // Prevent div by zero
                if (pos < half_period) {
                    val = (int16_t)(((pos * current_vol * 2) / half_period) - current_vol);
                } else {
                    val = (int16_t)(current_vol - (((pos - half_period) * current_vol * 2) / half_period));
                }
            } else if (channels[c].wave_type == 3) { // Noise
                int32_t mod_val = current_vol * 2;
                if (mod_val > 0) {
                    val = (int16_t)((_next_random() % mod_val) - current_vol);
                }
            }

            mixed_val += val;
            channels[c].phase++;
            channels[c].samples_played++;
        }
    }
    
    // Clip
    if (mixed_val > 32767) mixed_val = 32767;
    if (mixed_val < -32768) mixed_val = -32768;
    
    return mixed_val;
}

// For ESP32 (Interleaved Stereo, 16-bit)
void sound_synth_render_int16(int16_t* buffer, int num_samples) {
    bool all_silent = true;
    for (int c = 0; c < SOUND_SYNTH_MAX_CHANNELS; c++) {
        if (channels[c].freq > 0 && channels[c].volume > 0 && channels[c].samples_played < decay_samples) {
            all_silent = false;
            break;
        }
    }

    if (all_silent) {
        memset(buffer, 0, num_samples * 2 * sizeof(int16_t));
        return;
    }

    for (int i = 0; i < num_samples; i++) {
        int32_t mixed_val = sound_synth_mix_sample();
        buffer[i * 2]     = (int16_t)mixed_val; // L
        buffer[i * 2 + 1] = (int16_t)mixed_val; // R
    }
}

// For standard float buffers (e.g. general audio backends)
void sound_synth_render_float(float* out_l, float* out_r, int num_samples) {
    for (int i = 0; i < num_samples; i++) {
        int32_t mixed_val = sound_synth_mix_sample();
        float f_val = (float)mixed_val / 32768.0f;
        out_l[i] = f_val;
        out_r[i] = f_val;
    }
}

// For WASM AudioWorklet zero-copy memory access
static float wasm_render_buf_l[SOUND_SYNTH_WASM_RENDER_SIZE];
static float wasm_render_buf_r[SOUND_SYNTH_WASM_RENDER_SIZE];

float* sound_synth_get_wasm_buf_l(void) {
    return wasm_render_buf_l;
}

float* sound_synth_get_wasm_buf_r(void) {
    return wasm_render_buf_r;
}

void sound_synth_render_wasm(void) {
    sound_synth_render_float(wasm_render_buf_l, wasm_render_buf_r, SOUND_SYNTH_WASM_RENDER_SIZE);
}
