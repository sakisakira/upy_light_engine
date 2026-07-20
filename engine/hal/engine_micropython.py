from engine.framebuffer import screen

# ---- Window and Game Loop Management ----

def run(update, draw, fps=30):
    import engine.hal.st7789 as st7789
    from engine import time as engine_time
    display = st7789.ST7789(
        spi_id=1,
        baudrate=40000000,
        mosi=35,
        sck=36,
        cs=37,
        dc=34,
        rst=33,
        bl=38,
        width=240,
        height=135
    )
    import engine.input as input
    import utime as time
    import _lightengine
    
    # Inject screen into fb module explicitly
    import engine.framebuffer as fb
    fb.screen = screen
    
    input.init()
    _lightengine.init()
    
    target_ms = 1000 // fps
    
    import sys
    try:
        from engine.profiler import profiler
        import gc
        
        # Submit first empty frame to bootstrap pipeline
        screen.dl_idx = 1
        display.set_window(0, 0, 239, 134)
        _lightengine.submit_and_send(screen._c_fb, screen.dls[screen.dl_idx], None)
        
        while True:
            t0 = time.ticks_ms()
            engine_time.clock.tick()
            
            # Switch DisplayList
            screen.dl_idx = 1 - screen.dl_idx
            screen.dl_strings[screen.dl_idx].clear()
            screen.dl.clear()
            
            profiler.start("update")
            update()
            
            # Advance audio processing for SFX
            import engine.sound as sound
            sound.update()
            
            profiler.end("update")
            
            profiler.start("draw_all")
            draw()
            profiler.end("draw_all")
            
            # Wait for Core 1 to finish previous frame rendering
            profiler.start("sync")
            _lightengine.sync()
            profiler.end("sync")
            
            # Submit newly built display list for Core 1 to start rendering into CURRENT buffer AND sending it via SPI
            from engine.palette import colors565
            profiler.start("submit")
            _lightengine.submit_and_send(screen._c_fb, screen.dl, colors565)
            profiler.end("submit")
            
            # Print free memory every 600 frames to monitor leaks
            if engine_time.clock.frame_count % 600 == 0:
                print(f"FPS: {engine_time.clock.fps} | GC Free: {gc.mem_free()} bytes | FreeRTOS Free: {_lightengine.get_free_heap()} bytes")
                import micropython
                micropython.mem_info()
            
            profiler.start("sleep")
            t1 = time.ticks_ms()
            dt = time.ticks_diff(t1, t0)
            sleep_ms = target_ms - dt
            if sleep_ms > 0:
                # Sleep to yield CPU to FreeRTOS IDLE task (prevents Watchdog Timeout crash)
                if sleep_ms > 2:
                    time.sleep_ms(sleep_ms - 2)
                # Busy-wait the remaining time to avoid ESP32 RTOS tick rounding
                while time.ticks_diff(time.ticks_ms(), t0) < target_ms:
                    pass
            profiler.end("sleep")
    except Exception as e:
        with open('error.log', 'w') as f:
            sys.print_exception(e, f)
        raise
