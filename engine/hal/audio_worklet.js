class SoundSynthWorklet extends AudioWorkletProcessor {
    constructor(options) {
        super();
        this.wasm = null;
        this.buf_l_ptr = 0;
        this.buf_r_ptr = 0;
        this.memory_f32 = null;

        // Port message handler
        this.port.onmessage = (event) => {
            if (event.data.type === 'initWasm') {
                this.initWasm(event.data.wasmBytes);
            } else if (event.data.type === 'set_channel') {
                if (this.wasm) {
                    this.wasm.exports.sound_synth_set_channel(
                        event.data.ch,
                        event.data.freq,
                        event.data.wave_type,
                        event.data.volume
                    );
                }
            } else if (event.data.type === 'stop_all') {
                if (this.wasm) {
                    this.wasm.exports.sound_synth_stop_all();
                }
            }
        };
    }

    initWasm(wasmBytes) {
        WebAssembly.instantiate(wasmBytes, {}).then((result) => {
            this.wasm = result.instance;
            
            // Initialize synth with sample rate
            this.wasm.exports.sound_synth_init(sampleRate);
            
            // Get memory pointers for zero-copy access
            this.buf_l_ptr = this.wasm.exports.sound_synth_get_wasm_buf_l() / 4; // float32 index
            this.buf_r_ptr = this.wasm.exports.sound_synth_get_wasm_buf_r() / 4;
            
            // Create a Float32Array view over the WASM memory
            this.memory_f32 = new Float32Array(this.wasm.exports.memory.buffer);
            
            this.port.postMessage({ type: 'ready' });
        }).catch(err => {
            console.error("AudioWorklet: Failed to instantiate WASM", err);
        });
    }

    process(inputs, outputs, parameters) {
        const output = outputs[0];
        
        // If WASM is not loaded yet, just output silence
        if (!this.wasm || !this.memory_f32) {
            return true; 
        }

        const channelL = output[0];
        const channelR = output[1];
        
        // The WASM render function outputs SOUND_SYNTH_WASM_RENDER_SIZE (128) samples.
        // Web Audio API process() also expects exactly 128 samples per block.
        this.wasm.exports.sound_synth_render_wasm();
        
        // Ensure memory view is not detached (if WASM memory grew)
        if (this.memory_f32.buffer !== this.wasm.exports.memory.buffer) {
            this.memory_f32 = new Float32Array(this.wasm.exports.memory.buffer);
        }

        // Copy rendered data to output
        for (let i = 0; i < 128; i++) {
            channelL[i] = this.memory_f32[this.buf_l_ptr + i];
            if (channelR) {
                channelR[i] = this.memory_f32[this.buf_r_ptr + i];
            }
        }

        return true; // Keep processor alive
    }
}

registerProcessor('sound-synth-worklet', SoundSynthWorklet);
