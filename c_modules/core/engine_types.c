#include "engine_types.h"
#include <stddef.h>
#include <stdlib.h>
#include <assert.h>
DisplayList* dl_create(void) {
    DisplayList* dl = (DisplayList*)malloc(sizeof(DisplayList));
    if (dl) dl_init(dl);
    return dl;
}

void dl_destroy(DisplayList *display_list) {
    if (display_list) free(display_list);
}

#include "engine_types.h"
#include <stdio.h>
#include <string.h>

void dl_init(DisplayList *display_list) {
    if (display_list != NULL) {
        display_list->count = 0;
    }
}

void dl_clear(DisplayList *display_list) {
    if (display_list != NULL) {
        memset(display_list->commands, 0, sizeof(RenderCommand) * display_list->count);
        display_list->count = 0;
    }
}

void dl_push_clear(DisplayList *display_list, uint16_t color) {
    ENGINE_ASSERT_RETURN(display_list != NULL, "display_list is NULL");
    ENGINE_ASSERT_RETURN(display_list->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdClear;
    cmd->args.clear.color = color;
}

void dl_push_pset(DisplayList *display_list, int16_t x, int16_t y, uint16_t color) {
    ENGINE_ASSERT_RETURN(display_list != NULL, "display_list is NULL");
    ENGINE_ASSERT_RETURN(display_list->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdPset;
    cmd->args.pset.x = x;
    cmd->args.pset.y = y;
    cmd->args.pset.color = color;
}

void dl_push_line(DisplayList *display_list, int16_t x1, int16_t y1, int16_t x2, int16_t y2, uint16_t color) {
    ENGINE_ASSERT_RETURN(display_list != NULL, "display_list is NULL");
    ENGINE_ASSERT_RETURN(display_list->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdLine;
    cmd->args.line.x1 = x1;
    cmd->args.line.y1 = y1;
    cmd->args.line.x2 = x2;
    cmd->args.line.y2 = y2;
    cmd->args.line.color = color;
}

void dl_push_fill_rect(DisplayList *display_list, int16_t x, int16_t y,
                       int16_t w, int16_t h, uint16_t color) {
    ENGINE_ASSERT_RETURN(display_list != NULL, "display_list is NULL");
    ENGINE_ASSERT_RETURN(display_list->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdFillRect;
    cmd->args.fill_rect.x = x;
    cmd->args.fill_rect.y = y;
    cmd->args.fill_rect.w = w;
    cmd->args.fill_rect.h = h;
    cmd->args.fill_rect.color = color;
}

void dl_push_blt(DisplayList *display_list, int16_t x, int16_t y, EngineImage *img, int16_t u, int16_t v, int16_t w, int16_t h, uint16_t colkey, int tint) {
    ENGINE_ASSERT_RETURN(display_list != NULL, "display_list is NULL");
    ENGINE_ASSERT_RETURN(display_list->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdBlt;
    cmd->args.blt.x = x;
    cmd->args.blt.y = y;
    cmd->args.blt.img = img;
    cmd->args.blt.u = u;
    cmd->args.blt.v = v;
    cmd->args.blt.w = w;
    cmd->args.blt.h = h;
    cmd->args.blt.colkey = colkey;
    cmd->args.blt.tint = tint;
}

void dl_push_draw_sprite(DisplayList *dl, int16_t cx, int16_t cy, float scale, float angle,
                         EngineImage *img, int16_t u, int16_t v, int16_t w, int16_t h, uint16_t colkey, int tint) {
    ENGINE_ASSERT_RETURN(dl != NULL, "dl is NULL");
    ENGINE_ASSERT_RETURN(dl->count < kMaxCommands, "DisplayList command limit reached!");
    RenderCommand *cmd = &dl->commands[dl->count++];
    cmd->type = kCmdDrawSprite;
    cmd->args.draw_sprite.cx = cx;
    cmd->args.draw_sprite.cy = cy;
    cmd->args.draw_sprite.scale = scale;
    cmd->args.draw_sprite.angle = angle;
    cmd->args.draw_sprite.img = img;
    cmd->args.draw_sprite.u = u;
    cmd->args.draw_sprite.v = v;
    cmd->args.draw_sprite.w = w;
    cmd->args.draw_sprite.h = h;
    cmd->args.draw_sprite.colkey = colkey;
    cmd->args.draw_sprite.tint = tint;
}

void dl_push_draw_text(DisplayList *dl, int16_t x, int16_t y, EngineImage *font,
                       int char_w, int char_h, int columns,
                       const uint8_t *text, int text_len,
                       int16_t *lookup, int tint) {
    ENGINE_ASSERT_RETURN(dl != NULL, "dl is NULL");
    ENGINE_ASSERT_RETURN(dl->count < kMaxCommands, "DisplayList command limit reached!");
    ENGINE_ASSERT_RETURN(font != NULL, "font is NULL");
    ENGINE_ASSERT_RETURN(text != NULL, "text is NULL");
    
    RenderCommand *cmd = &dl->commands[dl->count++];
    cmd->type = kCmdDrawText;
    cmd->args.draw_text.x = x;
    cmd->args.draw_text.y = y;
    cmd->args.draw_text.font = font;
    cmd->args.draw_text.char_w = char_w;
    cmd->args.draw_text.char_h = char_h;
    cmd->args.draw_text.columns = columns;
    cmd->args.draw_text.text = text;
    cmd->args.draw_text.text_len = text_len;
    cmd->args.draw_text.lookup = lookup;
    cmd->args.draw_text.tint = tint;
}
