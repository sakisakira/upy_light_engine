#include "engine_types.h"
#include <stddef.h>

void dl_init(DisplayList *display_list) {
    if (display_list != NULL) {
        display_list->count = 0;
    }
}

void dl_clear(DisplayList *display_list) {
    if (display_list != NULL) {
        display_list->count = 0;
    }
}

void dl_push_clear(DisplayList *display_list, uint16_t color) {
    if (display_list == NULL || display_list->count >= kMaxCommands) return;
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdClear;
    cmd->args.clear.color = color;
}

void dl_push_fill_rect(DisplayList *display_list, int16_t x, int16_t y,
                       int16_t w, int16_t h, uint16_t color) {
    if (display_list == NULL || display_list->count >= kMaxCommands) return;
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdFillRect;
    cmd->args.fill_rect.x = x;
    cmd->args.fill_rect.y = y;
    cmd->args.fill_rect.w = w;
    cmd->args.fill_rect.h = h;
    cmd->args.fill_rect.color = color;
}

void dl_push_draw_sprite(DisplayList *display_list, int16_t cx, int16_t cy,
                         float scale, EngineSprite *sprite, int tint) {
    if (display_list == NULL || display_list->count >= kMaxCommands || sprite == NULL) return;
    RenderCommand *cmd = &display_list->commands[display_list->count++];
    cmd->type = kCmdDrawSprite;
    cmd->args.draw_sprite.cx = cx;
    cmd->args.draw_sprite.cy = cy;
    cmd->args.draw_sprite.scale = scale;
    cmd->args.draw_sprite.sprite = sprite;
    cmd->args.draw_sprite.tint = tint;
}

void dl_push_draw_text(DisplayList *display_list, int16_t x, int16_t y, EngineImage *font,
                       int char_w, int char_h, int columns,
                       const uint8_t *text, int text_len,
                       int16_t *lookup, int tint) {
    if (display_list == NULL || display_list->count >= kMaxCommands || font == NULL || text == NULL) return;
    RenderCommand *cmd = &display_list->commands[display_list->count++];
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
