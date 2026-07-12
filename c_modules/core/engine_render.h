#ifndef ENGINE_RENDER_H
#define ENGINE_RENDER_H

#include "engine_types.h"

// Execute a display list onto the framebuffer
void render_display_list(EngineFramebuffer *framebuffer,
                         DisplayList *display_list);

#endif // ENGINE_RENDER_H
