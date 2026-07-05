#ifndef ENGINE_TYPES_H
#define ENGINE_TYPES_H

#include <stdint.h>
#include <stdbool.h>

enum {
    kFormatRgb565 = 0,
    kFormatArgb4444 = 1,
    kFormatIndex8 = 2
};

// --- Data Structures ---

typedef struct {
    int16_t width;
    int16_t height;
    uint8_t format;
    uint8_t *data;
} EngineImage;

typedef struct {
    EngineImage *image;
    int16_t u;
    int16_t v;
    int16_t w;
    int16_t h;
    uint16_t colkey;
} EngineSprite;

typedef struct {
    int16_t width;
    int16_t height;
    uint8_t format;
    uint8_t *buffer;
} EngineFramebuffer;

// --- Display List Commands ---

typedef enum {
    kCmdClear,
    kCmdPset,
    kCmdLine,
    kCmdFillRect,
    kCmdBlt,
    kCmdDrawSprite,
    kCmdDrawText
} CommandType;

typedef struct {
    CommandType type;
    union {
        struct {
            uint16_t color;
        } clear;
        struct {
            int16_t x, y;
            uint16_t color;
        } pset;
        struct {
            int16_t x1, y1, x2, y2;
            uint16_t color;
        } line;
        struct {
            int16_t x, y, w, h;
            uint16_t color;
        } fill_rect;
        struct {
            int16_t x, y;
            EngineImage *img;
            int16_t u, v, w, h;
            uint16_t colkey;
            int tint;
        } blt;
        struct {
            int16_t cx, cy;
            float scale;
            float angle;
            EngineImage *img;
            int16_t u, v, w, h;
            uint16_t colkey;
            int tint;
        } draw_sprite;
        struct {
            int16_t x, y;
            EngineImage *font;
            int char_w, char_h, columns;
            const uint8_t *text;
            int text_len;
            int16_t *lookup;
            int tint;
        } draw_text;
    } args;
} RenderCommand;

enum { kMaxCommands = 256 };

typedef struct {
    RenderCommand commands[kMaxCommands];
    int count;
} DisplayList;

// --- API ---

// Initialize a display list
DisplayList* dl_create(void);
void dl_destroy(DisplayList *display_list);

void dl_init(DisplayList *display_list);
void dl_clear(DisplayList *display_list);

void dl_push_clear(DisplayList *display_list, uint16_t color);
void dl_push_pset(DisplayList *display_list, int16_t x, int16_t y, uint16_t color);
void dl_push_line(DisplayList *display_list, int16_t x1, int16_t y1, int16_t x2, int16_t y2, uint16_t color);
void dl_push_fill_rect(DisplayList *display_list, int16_t x, int16_t y, int16_t w, int16_t h, uint16_t color);
void dl_push_blt(DisplayList *display_list, int16_t x, int16_t y, EngineImage *img, int16_t u, int16_t v, int16_t w, int16_t h, uint16_t colkey, int tint);
void dl_push_draw_sprite(DisplayList *dl, int16_t cx, int16_t cy, float scale, float angle, EngineImage *img, int16_t u, int16_t v, int16_t w, int16_t h, uint16_t colkey, int tint);
void dl_push_draw_text(DisplayList *display_list, int16_t x, int16_t y, EngineImage *font,
                       int char_w, int char_h, int columns,
                       const uint8_t *text, int text_len,
                       int16_t *lookup, int tint);

#endif // ENGINE_TYPES_H
