import engine.framebuffer as fb
import engine.input as input
import engine.sound as sound
from engine.image import Image
from engine.font import Font
import random
from game_constants import *
from color_palette import *
from world import *
from physics import *
from stages import *
from background import *
from input import *
from play_record import *
from face import *
from status import *
from title import *
from result import *
from game_result import *
from sound import *
from music import *
from game_bike import GameBike

class GameGround:
    def __init__(self):
        # TODO / WORKAROUND (Performance):
        # In earlier versions, there was a method like `_update_world_ys` that calculated
        # and cached the Y-coordinates for the entire screen width into an array per frame.
        # These variables below were used for that purpose.
        # Currently, that pre-calculation logic has been lost. Instead, `screen_y(x)` is called
        # inside `show()` for every x-coordinate, generating thousands of Vec2 objects per frame.
        # This puts immense pressure on the GC, causing the game framerate to drop to 1 FPS.
        # We urgently need to restore and reimplement the array-based caching logic (e.g., using array('f')).
        # See `TODO.md` under "Performance Optimization" for more details.
        self.cached_world_ys = None
        self.world_x_min = None


    def ground(self):
        return g_stages[g_world.stage_index].ground

    def screen_y(self, screen_x):
        w_xy = g_world.world_xy(Vec2(screen_x, 0))
        w_y = self.ground().height(w_xy.x)
        s_xy = g_world.screen_xy(Vec2(w_xy.x, w_y))
        s_y = s_xy.y
        on_course = (w_xy.x <= self.ground().goal_x())
        return (s_xy.y, on_course)

    def color_index(self, screen_x):
        w_x = g_world.world_xy(Vec2(screen_x, 0)).x
        x = int(w_x) % 10
        if x < 5:
            return ColorPalette.Ground0
        else:
            return ColorPalette.Ground1

    def show(self):
        # WORKAROUND: Ground rendering was originally 1px per step using line().
        # It was changed to 8px steps using rect() to drastically reduce display list commands and CPU load.
        # This workaround degraded visual quality (blocky ground) and should be reviewed.
        step = 8
        for x in range(0, fb.screen.width, step):
            y, on_course = self.screen_y(x)
            if on_course:
                col = self.color_index(x)
            else:
                col = ColorPalette.GroundGoal
            y_int = int(y)
            surface_h = int(-g_world.rival_diff)
            surface_y = y_int - surface_h
            h = max(0, fb.screen.height - y_int)
            if h > 0:
                fb.screen.rect(x, y_int, step, h, col)
            if surface_h > 0:
                fb.screen.rect(x, surface_y, step, surface_h, ColorPalette.GroundSurface)

class App:
    BikeBodyImagePath = 'images/bike_body.uimg'
    TireImagePath = 'images/tire.uimg'
    CharaBodyImagePath = 'images/chara_body.uimg'
    CharaSymbolImagePath = 'images/chara_symbol.uimg'
    FacesImagePath = 'images/faces.uimg'
    TitleCharaImagePath = 'images/title_chara.uimg'
    TitleTextImagePath = 'images/title_text.uimg'
    ResultCharaImagePath = 'images/result_chara.uimg'
    
    def __init__(self):
        
        self.color_palette = ColorPalette(
            [self.BikeBodyImagePath,
             self.TireImagePath,
             self.CharaBodyImagePath,
             self.CharaSymbolImagePath],
            [self.FacesImagePath,
             self.TitleCharaImagePath,
             self.TitleTextImagePath,
             self.ResultCharaImagePath])

        # Initialize image buffer and palette AT STARTUP
        import sys
        import engine.image as image
        if sys.platform == 'esp32':
            # Cardputer Adv: Do not use static buffer, allow dynamic GC allocation to avoid contiguous MemoryError
            image.set_global_buffer_manager(None)
            
            # Load Palette directly into engine's global palette
            try:
                import engine.palette as engine_palette
                with open("images/palette.bin", "rb") as f:
                    f.readinto(engine_palette.colors565)
            except Exception as e:
                print("Failed to load palette:", e)
        else:
            fb_size = 46 * 1024 # 46KB for images
            image.set_global_buffer_manager(image.ImageBufferManager(fb_size))
            
            # Load Palette
            try:
                import struct
                import engine.palette as engine_palette
                with open("images/palette.bin", "rb") as f:
                    palette_data = f.read(512)
                for i in range(256):
                    c1 = palette_data[i*2]
                    c2 = palette_data[i*2+1]
                    rgb565 = (c1 << 8) | c2
                    r = (rgb565 >> 11) & 0x1F
                    g = (rgb565 >> 5) & 0x3F
                    b = rgb565 & 0x1F
                    r = (r * 255) // 31
                    g = (g * 255) // 63
                    b = (b * 255) // 31
                    engine_palette.colors[i] = (r << 16) | (g << 8) | b
            except Exception as e:
                print("Failed to load palette:", e)

        self.state = GameState.GameTitle
        self.title = Title(
            self.TitleCharaImagePath,
            self.TitleTextImagePath)
        self.game_result = GameResult(self.ResultCharaImagePath)
        self.bike = GameBike(
            self.BikeBodyImagePath,
            self.TireImagePath,
            self.CharaBodyImagePath,
            self.CharaSymbolImagePath)
        self.bike_rival = GameBike(
            self.BikeBodyImagePath,
            self.TireImagePath,
            self.CharaBodyImagePath,
            self.CharaSymbolImagePath,
            self.color_palette.gray_converter())
        self.ground = GameGround()
        g_world.start()
        self.input = Input()
        self.play_record = PlayRecord()
        self.play_record_rival = None
        self.face = Face(path = self.FacesImagePath)
        self.status = Status()
        self.result = Result()
        self.sound = Sound(sound_index = 0)
        self.music = Music(sound_index = 1)
        self.reset()
        
        # Free up memory from module imports before loading images
        try:
            import gc
            gc.collect()
        except:
            pass
            
        self.title.load()
        import engine
        engine.run(self.update, self.draw, fps=g_world.fps)

    def stage(self):
        return g_stages[g_world.stage_index]

    def bike_x_diff(self):
        diff_max = g_world.origin_screen.x
        v_max = self.bike.bike.max_speed
        v = self.bike.bike.velocity.x
        return v / v_max * diff_max / g_world.scale.x

    def goal_distance(self):
        return self.stage().ground.goal_x() - self.bike.bike.location.x

    def update_face(self, in_game, succeeded):
        if in_game:
            self.face.update(self.bike.face_index())
        else:
            if succeeded:
                self.face.update(FaceIndex.Smile)
            else:
                self.face.update(FaceIndex.Cry)

    def update_in_game(self):
        self.background.update(g_world.origin_world.x)
        bike = self.bike.bike
        ox = bike.location.x + self.bike_x_diff()
        tic = g_world.tic
        g_world.update(Vec2(ox, 0))
        self.input.update(True)
        btn_a = self.input.a_pressed
        btn_b = self.input.b_pressed
        self.play_record.add(btn_a, btn_b)
        self.bike.update(self.stage().ground, btn_a, btn_b)
        if self.play_record_rival:
            btn_r = self.play_record_rival.recorded_buttons(tic)
            self.bike_rival.update(self.stage().ground, btn_r[0], btn_r[1])
        self.status.update(self.bike.bike, self.stage().ground)
        self.update_face(True, False)
        self.result.update(False, False)
        if self.input.x_pressed:
            self.reset()

    def update_result(self, failed, result_time):
        self.input.update(False)
        if failed:
            self.bike.update_chara_body_index(CharaBodyIndex.Failed)
        else:
            self.bike.update_chara_body_index(CharaBodyIndex.Succeeded)
        self.result.update(failed, result_time)
        self.update_face(False, not failed)
        if self.input.x_pressed:
            if result_time:
                stage = self.stage()
                stage_index = g_world.stage_index
                stage.update_best_time(stage_index, result_time, self.play_record)
                s_i = (stage_index + 1) % len(g_stages)
                g_world.stage_index = s_i
                if s_i == 0:
                    # TODO (Refactor): This raw memory management logic (sync, unload, gc, buffer reset)
                    # is unintuitive and pollutes the game logic. It should be refactored using a scene 
                    # transition helper or callback (e.g., `onStageChanged`) provided by the engine in the future.
                    try:
                        import _lightengine; _lightengine.sync()
                    except ImportError:
                        pass
                    self.bike.unload()
                    self.bike_rival.unload()
                    # Initialize images buffer
                    import sys
                    if sys.platform == 'esp32':
                        # Cardputer Adv: Do not use static buffer
                        image.set_global_buffer_manager(None)
                        
                        # Load Palette directly into engine's global palette
                        try:
                            import engine.palette as engine_palette
                            with open("images/palette.bin", "rb") as f:
                                f.readinto(engine_palette.colors565)
                        except Exception as e:
                            print("Failed to load palette:", e)
                    else:
                        fb_size = 50 * 1024 # 50KB for images
                        image.set_global_buffer_manager(image.ImageBufferManager(fb_size))
                        
                        # Load Palette
                        try:
                            import struct
                            import engine.palette as engine_palette
                            with open("images/palette.bin", "rb") as f:
                                palette_data = f.read(512)
                            for i in range(256):
                                # palette.bin is rgb565 big endian
                                c1 = palette_data[i*2]
                                c2 = palette_data[i*2+1]
                                rgb565 = (c1 << 8) | c2
                                r = (rgb565 >> 11) & 0x1F
                                g = (rgb565 >> 5) & 0x3F
                                b = rgb565 & 0x1F
                                r = (r * 255) // 31
                                g = (g * 255) // 63
                                b = (b * 255) // 31
                                engine_palette.colors[i] = (r << 16) | (g << 8) | b
                        except Exception as e:
                            print("Failed to load palette:", e)
                    self.face.unload()
                    import gc; gc.collect()
                    import engine.image as image
                    image.Image.clear_cache()
                    if image._global_buffer_manager:
                        image._global_buffer_manager.reset()

                    self.game_result.load()
                    self.state = GameState.GameResult
                    self.game_result.reset()
                    self.reset()
                    return
            self.reset()

    def update(self):
        if self.state == GameState.GameTitle:
            self.title.update()
            if self.title.start_pressed():
                # TODO (Refactor): This raw memory management logic (sync, unload, gc, buffer reset)
                # is unintuitive and pollutes the game logic. It should be refactored using a scene 
                # transition helper or callback (e.g., `onStageChanged`) provided by the engine in the future.
                try:
                    import _lightengine; _lightengine.sync()
                except ImportError:
                    pass
                self.title.unload()
                
                # WORKAROUND: MicroPython's conservative GC keeps old Image objects alive 
                # if their pointers remain in the C DisplayList memory after dl_clear().
                # We push dummy commands to overwrite any old image pointers in BOTH display lists.
                import engine.framebuffer as fb
                for _ in range(2):
                    for _ in range(50):
                        fb.screen.rect(0, 0, 1, 1, 0)
                # Display list is flushed automatically at the end of the frame
                    
                import gc; gc.collect()
                import engine.image as image
                image.Image.clear_cache()
                if image._global_buffer_manager:
                    image._global_buffer_manager.reset()

                self.bike.load()
                self.bike_rival.load()
                self.face.load()

                self.state = GameState.GamePlay
                self.reset()
        elif self.state == GameState.GamePlay:
            failed = self.bike.failed()
            if self.goal_distance() <= 0:
                result_time = g_world.elapsed_time
            else:
                result_time = False
            if failed or result_time:

                self.music.stop()
                self.update_result(failed, result_time)
                self.sound.update(False)
            else:
                self.update_in_game()
                self.sound.update(self.bike.bike.speed_ratio())
        elif self.state == GameState.GameResult:
            self.game_result.update()
            if self.game_result.pressed():
                self.to_title()
        else:
            raise

    def draw(self):
        if self.state == GameState.GameTitle:
            self.title.show()
        elif self.state == GameState.GamePlay:
            self.background.show()
            self.ground.show()
            if self.play_record_rival:
                self.bike_rival.show()
            self.bike.show()
            self.input.show()
            self.face.show()
            self.status.show()
            self.result.show()
        elif self.state == GameState.GameResult:
            self.game_result.show()
        else:
            raise

    def reset(self):
        g_world.start()
        index = g_world.stage_index
        self.stage().start()
        if not hasattr(self, 'background') or not hasattr(self.background, 'stage_index') or self.background.stage_index != index:
            import gc
            gc.collect()
            import background
            self.background = background.Background()
            self.background.stage_index = index
            gc.collect()
        
        self.play_record.reset()
        if g_savedata.record_a(index):
            rec_a = g_savedata.record_a(index)
            rec_b = g_savedata.record_b(index)
            self.play_record_rival = PlayRecord(rec_a, rec_b)
        else:
            self.play_record_rival = None
            
        if self.state == GameState.GamePlay:
            # TODO (Refactor): Loading assets inside `reset()` is bad practice (it causes double-loads
            # and mixes memory management with game state resets). This entire block (including the GC 
            # and background initialization above) should be moved to a scene transition helper 
            # like `onStageChanged` or `onStageEnter` in the future.
            self.bike.load()
            self.bike_rival.load()
            self.face.load()
            self.bike.bike.reset()
            self.bike_rival.bike.reset()
            self.music.play(self.stage().music)
        elif self.state == GameState.GameTitle:
            self.bike.bike.reset()
            self.bike_rival.bike.reset()
            self.music.play(Music.TitleMusicIndex)
        elif self.state == GameState.GameResult:
            self.music.play(Music.ResultMusicIndex)
        else:
            # WORKAROUND: Fallback for unknown states.
            # In the original Pyxel version, this was `raise()` to crash on invalid states.
            # Here, it is changed to `self.music.play(-1)` (stop music) to avoid hard crashes
            # in the microcontroller environment if an unexpected state occurs.
            # TODO (Refactor): Once the engine provides a safe assertion mechanism (e.g., `engine.assert_()`)
            # that displays an error screen without freezing the device, replace this fallback with an assertion.
            self.music.play(-1)

    def to_title(self):
        # TODO (Refactor): This raw memory management logic (sync, unload, gc, buffer reset)
        # is unintuitive and pollutes the game logic. It should be refactored using a scene 
        # transition helper or callback (e.g., `onStageChanged`) provided by the engine in the future.
        try:
            import _lightengine; _lightengine.sync()
        except ImportError:
            pass
        self.game_result.unload()
        
        # WORKAROUND: MicroPython's conservative GC keeps old Image objects alive 
        # if their pointers remain in the C DisplayList memory after dl_clear().
        # We push dummy commands to overwrite any old image pointers in BOTH display lists.
        import engine.framebuffer as fb
        for _ in range(2):
            for _ in range(50):
                fb.screen.rect(0, 0, 1, 1, 0)
        # Display list is flushed automatically at the end of the frame
            
        import gc; gc.collect()
        import engine.image as image
        image.Image.clear_cache()
        if image._global_buffer_manager:
            image._global_buffer_manager.reset()

        self.title.load()

        self.title.reset()
        self.state = GameState.GameTitle
        self.reset()
        
App()
