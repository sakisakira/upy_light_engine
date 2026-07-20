#include "sound_synth.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>
#include <stdio.h>
#include "py/mpprint.h"

#ifdef ESP_PLATFORM
#include "esp_heap_caps.h"
#endif

static sound_synth_channel_t channels[SOUND_SYNTH_MAX_CHANNELS];
static int current_sample_rate = 44100;
static sound_synth_ubgm_t ubgm_seq = {0};

// LCG PRNG
static uint32_t _random_seed = 12345;
static uint32_t _next_random() {
    _random_seed = _random_seed * 1664525 + 1013904223;
    return _random_seed;
}

void sound_synth_init(int sample_rate) {
    current_sample_rate = sample_rate;
    
    // Clear state
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
    ubgm_seq.is_playing = false;
}

void sound_synth_set_channel_override(int ch, bool override) {
    if (ch >= 0 && ch < SOUND_SYNTH_MAX_CHANNELS) {
        ubgm_seq.tracks[ch].overridden = override;
    }
}

static void _ubgm_fetch_next_note(int ch) {
    if (!ubgm_seq.is_playing || !ubgm_seq.data) return;
    
    if (ubgm_seq.tracks[ch].notes_remaining == 0) {
        // Track finished current segment
        uint32_t track_header = 16 + ch * 12; // 16-byte main header, 12-byte per-track header
        if (track_header + 12 > ubgm_seq.length) return; // Invalid
        
        // uint16_t ic = ubgm_seq.data[track_header] | (ubgm_seq.data[track_header+1] << 8); // unused
        uint16_t lc = ubgm_seq.data[track_header+2] | (ubgm_seq.data[track_header+3] << 8);
        // uint32_t io = ubgm_seq.data[track_header+4] | (ubgm_seq.data[track_header+5] << 8) | (ubgm_seq.data[track_header+6] << 16) | (ubgm_seq.data[track_header+7] << 24); // unused
        uint32_t lo = ubgm_seq.data[track_header+8] | (ubgm_seq.data[track_header+9] << 8) | (ubgm_seq.data[track_header+10] << 16) | (ubgm_seq.data[track_header+11] << 24);
        
        if (!ubgm_seq.tracks[ch].is_looping && lc > 0) {
            // Transition to loop
            ubgm_seq.tracks[ch].is_looping = true;
            ubgm_seq.tracks[ch].current_offset = lo;
            ubgm_seq.tracks[ch].notes_remaining = lc;
        } else if (ubgm_seq.tracks[ch].is_looping) {
            // Re-loop
            ubgm_seq.tracks[ch].current_offset = lo;
            ubgm_seq.tracks[ch].notes_remaining = lc;
        } else {
            // Done
            if (!ubgm_seq.tracks[ch].overridden) {
                sound_synth_set_channel(ch, 0, 0, 0);
            }
            return;
        }
    }
    
    if (ubgm_seq.tracks[ch].notes_remaining > 0) {
        uint32_t off = ubgm_seq.tracks[ch].current_offset;
        if (off + 6 <= ubgm_seq.length) {
            uint16_t freq = ubgm_seq.data[off] | (ubgm_seq.data[off+1] << 8);
            uint16_t dur_ms = ubgm_seq.data[off+2] | (ubgm_seq.data[off+3] << 8);
            uint8_t vol = ubgm_seq.data[off+4];
            uint8_t wave = ubgm_seq.data[off+5];
            
            uint32_t total = (uint32_t)dur_ms * (current_sample_rate / 1000);
            ubgm_seq.tracks[ch].samples_until_next = total;
            ubgm_seq.tracks[ch].total_samples = total;
            
            if (!ubgm_seq.tracks[ch].overridden) {
                sound_synth_set_channel(ch, freq, wave, vol);
            }
            
            ubgm_seq.tracks[ch].current_offset += 6;
            ubgm_seq.tracks[ch].notes_remaining--;
        } else {
            ubgm_seq.tracks[ch].notes_remaining = 0; // Error
        }
    }
}

bool sound_synth_play_ubgm(const uint8_t* data, size_t length) {
    if (length < 16) {
        mp_printf(&mp_plat_print, "UBGM Error: length %u < 16\n", (unsigned int)length);
        ubgm_seq.is_playing = false;
        return false;
    }
    
    if (ubgm_seq.data) {
        // DO NOT FREE! The buffer is managed by Python (either pre-allocated or kept alive)
        // heap_caps_free(ubgm_seq.data);
        ubgm_seq.data = NULL;
    }
    
#ifdef ESP_PLATFORM
    mp_printf(&mp_plat_print, "[sound_synth] heap_caps_get_free_size = %u\n", (unsigned int)heap_caps_get_free_size(MALLOC_CAP_8BIT));
#endif

    // Direct pointer assignment (no allocation/copy)
    ubgm_seq.data = (uint8_t*)data;
    ubgm_seq.length = length;
    
    // Reset tracks
    for (int ch = 0; ch < SOUND_SYNTH_MAX_CHANNELS; ch++) {
        ubgm_seq.tracks[ch].is_looping = false;
        ubgm_seq.tracks[ch].notes_remaining = 0;
        ubgm_seq.tracks[ch].samples_until_next = 0;
        ubgm_seq.tracks[ch].total_samples = 0;
        ubgm_seq.tracks[ch].overridden = false;
        
        uint32_t track_header = 16 + ch * 12;
        if (track_header + 12 <= length) {
            uint16_t ic = ubgm_seq.data[track_header] | (ubgm_seq.data[track_header+1] << 8);
            uint32_t io = ubgm_seq.data[track_header+4] | (ubgm_seq.data[track_header+5] << 8) | (ubgm_seq.data[track_header+6] << 16) | (ubgm_seq.data[track_header+7] << 24);
            
            if (ic > 0) {
                ubgm_seq.tracks[ch].current_offset = io;
                ubgm_seq.tracks[ch].notes_remaining = ic;
                
                if (io >= length || io + ic * 6 > length) { // Validate track offset and size
                    mp_printf(&mp_plat_print, "UBGM Error: track %d intro invalid (io=%u, ic=%u, length=%u)\n", ch, (unsigned int)io, (unsigned int)ic, (unsigned int)length);
                    return false;
                }
            }
            
            uint16_t lc = ubgm_seq.data[track_header+2] | (ubgm_seq.data[track_header+3] << 8);
            uint32_t lo = ubgm_seq.data[track_header+8] | (ubgm_seq.data[track_header+9] << 8) | (ubgm_seq.data[track_header+10] << 16) | (ubgm_seq.data[track_header+11] << 24);
            
            if (lc > 0) {
                if (lo >= length || lo + lc * 6 > length) { // Validate track offset and size
                    mp_printf(&mp_plat_print, "UBGM Error: track %d loop invalid (lo=%u, lc=%u, length=%u)\n", ch, (unsigned int)lo, (unsigned int)lc, (unsigned int)length);
                    return false;
                }
            } else {
                // If no intro, start from loop immediately by forcing is_looping=false and notes_remaining=0
                // the fetch function will naturally jump to loop.
            }
        }
    }
    
    ubgm_seq.is_playing = true;
    for (int ch = 0; ch < SOUND_SYNTH_MAX_CHANNELS; ch++) {
        _ubgm_fetch_next_note(ch);
    }
    
    return true;
}

// Core synthesis calculation for a single sample
static int32_t sound_synth_mix_sample(void) {
    int32_t mixed_val = 0;
    
    // Process UBGM sequencer
    if (ubgm_seq.is_playing) {
        for (int c = 0; c < SOUND_SYNTH_MAX_CHANNELS; c++) {
            if (ubgm_seq.tracks[c].samples_until_next > 0) {
                ubgm_seq.tracks[c].samples_until_next--;
                if (ubgm_seq.tracks[c].samples_until_next == 0) {
                    _ubgm_fetch_next_note(c);
                }
            }
        }
    }
    
    for (int c = 0; c < SOUND_SYNTH_MAX_CHANNELS; c++) {
        if (channels[c].freq > 0 && channels[c].volume > 0) {
            uint32_t period = current_sample_rate / channels[c].freq;
            if (period == 0) continue;
            
            float env = 1.0f;
            uint32_t played = channels[c].samples_played;
            uint32_t decay_len = current_sample_rate / 2; // 0.5s decay
            
            // Sustain level: 0.0 for noise (percussion), 0.4 for other waveforms
            float sustain = (channels[c].wave_type == 3) ? 0.0f : 0.4f;
            
            if (played < decay_len) {
                float decay_factor = 1.0f - ((float)played / (float)decay_len);
                env = sustain + (1.0f - sustain) * decay_factor;
            } else {
                env = sustain;
            }
            
            // Apply note separation gap at the end (if not overridden by SFX)
            if (ubgm_seq.is_playing && !ubgm_seq.tracks[c].overridden) {
                uint32_t remaining = ubgm_seq.tracks[c].samples_until_next;
                uint32_t total = ubgm_seq.tracks[c].total_samples;
                uint32_t gap_len = current_sample_rate / 20; // 50ms envelope
                if (total / 2 < gap_len) {
                    gap_len = total / 2;
                }
                
                if (remaining < gap_len && gap_len > 0) {
                    env = env * ((float)remaining / (float)gap_len);
                }
            }
            
            int32_t current_vol = (int32_t)(channels[c].volume * 30 * env);
            
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
    bool all_silent = !ubgm_seq.is_playing;
    
    if (all_silent) {
        for (int c = 0; c < SOUND_SYNTH_MAX_CHANNELS; c++) {
            if (channels[c].freq > 0 && channels[c].volume > 0) {
                all_silent = false;
                break;
            }
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
