#include "py/runtime.h"
#include "py/obj.h"
#include "engine_render.h"
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <freertos/queue.h>
#include <driver/spi_master.h>
#include <driver/gpio.h>
#include <esp_heap_caps.h>
#include <esp_timer.h>
#include <string.h>

#include "engine_types.h"
#include "core/engine_render.h"

// Helper to accept both ints and floats for coordinates/dimensions
static int32_t get_int_from_obj(mp_obj_t obj) {
    if (mp_obj_is_float(obj)) {
        return (int32_t)mp_obj_get_float(obj);
    }
    return (int32_t)mp_obj_get_int(obj);
}

// --- Image Type ---
typedef struct _lightengine_Image_obj_t {
    mp_obj_base_t base;
    EngineImage img;
} lightengine_Image_obj_t;


static mp_obj_t image_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 3, 4, false);
    lightengine_Image_obj_t *self = m_new_obj(lightengine_Image_obj_t);
    self->base.type = type;
    self->img.width = mp_obj_get_int(args[0]);
    self->img.height = mp_obj_get_int(args[1]);
    self->img.format = mp_obj_get_int(args[2]);
    
    if (n_args >= 4) {
        mp_buffer_info_t bufinfo;
        mp_get_buffer_raise(args[3], &bufinfo, MP_BUFFER_READ);
        self->img.data = bufinfo.buf;
    } else {
        size_t size = self->img.width * self->img.height;
        if (self->img.format == kFormatArgb4444) size *= 2;
        self->img.data = m_new(uint8_t, size);
    }
    
    return MP_OBJ_FROM_PTR(self);
}

static void image_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    lightengine_Image_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL) {
        if (attr == MP_QSTR_width) dest[0] = MP_OBJ_NEW_SMALL_INT(self->img.width);
        else if (attr == MP_QSTR_height) dest[0] = MP_OBJ_NEW_SMALL_INT(self->img.height);
        else if (attr == MP_QSTR_format) dest[0] = MP_OBJ_NEW_SMALL_INT(self->img.format);
    }
}

static MP_DEFINE_CONST_OBJ_TYPE(
    lightengine_Image_type,
    MP_QSTR_Image,
    MP_TYPE_FLAG_NONE,
    make_new, image_make_new,
    attr, image_attr
);

// --- Sprite Type ---
typedef struct _lightengine_Sprite_obj_t {
    mp_obj_base_t base;
    EngineSprite sprite;
} lightengine_Sprite_obj_t;


static mp_obj_t sprite_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 5, 6, false);
    lightengine_Sprite_obj_t *self = m_new_obj(lightengine_Sprite_obj_t);
    self->base.type = type;
    
    lightengine_Image_obj_t *img = MP_OBJ_TO_PTR(args[0]);
    self->sprite.image = &img->img;
    self->sprite.u = mp_obj_get_int(args[1]);
    self->sprite.v = mp_obj_get_int(args[2]);
    self->sprite.w = mp_obj_get_int(args[3]);
    self->sprite.h = mp_obj_get_int(args[4]);
    self->sprite.colkey = (n_args > 5) ? mp_obj_get_int(args[5]) : 0;
    
    return MP_OBJ_FROM_PTR(self);
}

static void sprite_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    lightengine_Sprite_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL) {
        // Load
        if (attr == MP_QSTR_u) dest[0] = MP_OBJ_NEW_SMALL_INT(self->sprite.u);
        else if (attr == MP_QSTR_v) dest[0] = MP_OBJ_NEW_SMALL_INT(self->sprite.v);
        else if (attr == MP_QSTR_w) dest[0] = MP_OBJ_NEW_SMALL_INT(self->sprite.w);
        else if (attr == MP_QSTR_h) dest[0] = MP_OBJ_NEW_SMALL_INT(self->sprite.h);
        else if (attr == MP_QSTR_colkey) dest[0] = MP_OBJ_NEW_SMALL_INT(self->sprite.colkey);
    } else {
        // Store
        if (attr == MP_QSTR_u) { self->sprite.u = mp_obj_get_int(dest[1]); dest[0] = MP_OBJ_NULL; }
        else if (attr == MP_QSTR_v) { self->sprite.v = mp_obj_get_int(dest[1]); dest[0] = MP_OBJ_NULL; }
        else if (attr == MP_QSTR_w) { self->sprite.w = mp_obj_get_int(dest[1]); dest[0] = MP_OBJ_NULL; }
        else if (attr == MP_QSTR_h) { self->sprite.h = mp_obj_get_int(dest[1]); dest[0] = MP_OBJ_NULL; }
        else if (attr == MP_QSTR_colkey) { self->sprite.colkey = mp_obj_get_int(dest[1]); dest[0] = MP_OBJ_NULL; }
    }
}

static MP_DEFINE_CONST_OBJ_TYPE(
    lightengine_Sprite_type,
    MP_QSTR_Sprite,
    MP_TYPE_FLAG_NONE,
    make_new, sprite_make_new,
    attr, sprite_attr
);

// --- Framebuffer Type ---
typedef struct _lightengine_Framebuffer_obj_t {
    mp_obj_base_t base;
    EngineFramebuffer fb;
} lightengine_Framebuffer_obj_t;


static mp_obj_t framebuffer_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 3, 4, false);
    lightengine_Framebuffer_obj_t *self = m_new_obj(lightengine_Framebuffer_obj_t);
    self->base.type = type;
    self->fb.width = mp_obj_get_int(args[0]);
    self->fb.height = mp_obj_get_int(args[1]);
    self->fb.format = mp_obj_get_int(args[2]);
    
    if (n_args >= 4 && args[3] != mp_const_none) {
        mp_buffer_info_t bufinfo;
        mp_get_buffer_raise(args[3], &bufinfo, MP_BUFFER_RW);
        self->fb.buffer = bufinfo.buf;
    } else {
        size_t size = self->fb.width * self->fb.height;
        if (self->fb.format == kFormatArgb4444 || self->fb.format == kFormatRgb565) size *= 2;
        self->fb.buffer = heap_caps_malloc(size, MALLOC_CAP_DMA | MALLOC_CAP_8BIT);
        if (self->fb.buffer == NULL) {
            mp_raise_msg(&mp_type_MemoryError, MP_ROM_QSTR(MP_QSTR_Failed_to_allocate_framebuffer_on_C_heap));
        }
        memset(self->fb.buffer, 0, size);
    }
    
    return MP_OBJ_FROM_PTR(self);
}

static void framebuffer_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest) {
    lightengine_Framebuffer_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL) {
        if (attr == MP_QSTR_width) dest[0] = MP_OBJ_NEW_SMALL_INT(self->fb.width);
        else if (attr == MP_QSTR_height) dest[0] = MP_OBJ_NEW_SMALL_INT(self->fb.height);
        else if (attr == MP_QSTR_format) dest[0] = MP_OBJ_NEW_SMALL_INT(self->fb.format);
    }
}

static MP_DEFINE_CONST_OBJ_TYPE(
    lightengine_Framebuffer_type,
    MP_QSTR_Framebuffer,
    MP_TYPE_FLAG_NONE,
    make_new, framebuffer_make_new,
    attr, framebuffer_attr
);

// --- DisplayList Type ---
typedef struct _lightengine_DisplayList_obj_t {
    mp_obj_base_t base;
    DisplayList *dl;
} lightengine_DisplayList_obj_t;


static mp_obj_t dl_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = m_new_obj(lightengine_DisplayList_obj_t);
    self->base.type = type;
    
    // Allocate DisplayList from C standard heap (malloc) to save MicroPython GC heap
    self->dl = dl_create();
    if (self->dl == NULL) {
        mp_raise_msg(&mp_type_MemoryError, MP_ROM_QSTR(MP_QSTR_Failed_to_allocate_DisplayList));
    }
    
    return MP_OBJ_FROM_PTR(self);
}

static mp_obj_t dl_clear_meth(mp_obj_t self_in) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(self_in);
    dl_clear(self->dl);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(dl_clear_obj, dl_clear_meth);

static mp_obj_t dl_meth_push_clear(mp_obj_t self_in, mp_obj_t color_in) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(self_in);
    dl_push_clear(self->dl, mp_obj_get_int(color_in));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(dl_push_clear_obj, dl_meth_push_clear);

static mp_obj_t dl_meth_push_pset(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t x = get_int_from_obj(args[1]);
    int32_t y = get_int_from_obj(args[2]);
    if (!is_visible(x, y, 1, 1)) return mp_const_none;
    dl_push_pset(self->dl, sanitize_x(x), sanitize_y(y), mp_obj_get_int(args[3]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_pset_obj, 4, 4, dl_meth_push_pset);

static mp_obj_t dl_meth_push_line(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t x1 = get_int_from_obj(args[1]);
    int32_t y1 = get_int_from_obj(args[2]);
    int32_t x2 = get_int_from_obj(args[3]);
    int32_t y2 = get_int_from_obj(args[4]);
    
    int32_t min_x = (x1 < x2) ? x1 : x2;
    int32_t max_x = (x1 > x2) ? x1 : x2;
    int32_t min_y = (y1 < y2) ? y1 : y2;
    int32_t max_y = (y1 > y2) ? y1 : y2;
    if (!is_visible(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)) return mp_const_none;
    
    dl_push_line(self->dl, sanitize_x(x1), sanitize_y(y1), sanitize_x(x2), sanitize_y(y2), mp_obj_get_int(args[5]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_line_obj, 6, 6, dl_meth_push_line);

static mp_obj_t dl_meth_push_fill_rect(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t x = get_int_from_obj(args[1]);
    int32_t y = get_int_from_obj(args[2]);
    int32_t w = get_int_from_obj(args[3]);
    int32_t h = get_int_from_obj(args[4]);
    if (!is_visible(x, y, w, h)) return mp_const_none;
    
    dl_push_fill_rect(self->dl, sanitize_x(x), sanitize_y(y), (int16_t)w, (int16_t)h, mp_obj_get_int(args[5]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_fill_rect_obj, 6, 6, dl_meth_push_fill_rect);

static mp_obj_t dl_meth_push_draw_sprite(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t cx = get_int_from_obj(args[1]);
    int32_t cy = get_int_from_obj(args[2]);
    float scale = mp_obj_get_float(args[3]);
    float angle = mp_obj_get_float(args[4]);
    lightengine_Image_obj_t *img = MP_OBJ_TO_PTR(args[5]);
    int32_t u = get_int_from_obj(args[6]);
    int32_t v = get_int_from_obj(args[7]);
    int32_t w = get_int_from_obj(args[8]);
    int32_t h = get_int_from_obj(args[9]);
    int colkey = mp_obj_get_int(args[10]);
    int tint = mp_obj_get_int(args[11]);
    
    int32_t scaled_w = (int32_t)(w * scale);
    int32_t scaled_h = (int32_t)(h * scale);
    if (!is_visible(cx - scaled_w/2, cy - scaled_h/2, scaled_w, scaled_h)) return mp_const_none;
    
    dl_push_draw_sprite(self->dl, sanitize_x(cx), sanitize_y(cy), scale, angle, &img->img, (int16_t)u, (int16_t)v, (int16_t)w, (int16_t)h, colkey, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_draw_sprite_obj, 12, 12, dl_meth_push_draw_sprite);

static mp_obj_t dl_meth_push_blt(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t x = get_int_from_obj(args[1]);
    int32_t y = get_int_from_obj(args[2]);
    lightengine_Image_obj_t *img = MP_OBJ_TO_PTR(args[3]);
    int32_t u = get_int_from_obj(args[4]);
    int32_t v = get_int_from_obj(args[5]);
    int32_t w = get_int_from_obj(args[6]);
    int32_t h = get_int_from_obj(args[7]);
    int colkey = mp_obj_get_int(args[8]);
    int tint = mp_obj_get_int(args[9]);
    
    if (!is_visible(x, y, w, h)) return mp_const_none;
    
    dl_push_blt(self->dl, sanitize_x(x), sanitize_y(y), &img->img, (int16_t)u, (int16_t)v, (int16_t)w, (int16_t)h, colkey, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_blt_obj, 10, 10, dl_meth_push_blt);

static mp_obj_t dl_meth_push_draw_text(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int32_t x = get_int_from_obj(args[1]);
    int32_t y = get_int_from_obj(args[2]);
    lightengine_Image_obj_t *font = MP_OBJ_TO_PTR(args[3]);
    int32_t char_w = get_int_from_obj(args[4]);
    int32_t char_h = get_int_from_obj(args[5]);
    int columns = get_int_from_obj(args[6]);
    
    mp_buffer_info_t text_bufinfo;
    mp_get_buffer_raise(args[7], &text_bufinfo, MP_BUFFER_READ);
    const uint8_t *text = text_bufinfo.buf;
    int text_len = text_bufinfo.len;
    
    int32_t text_total_w = char_w * text_len; // simple estimation for single line text
    if (!is_visible(x, y, text_total_w, char_h)) return mp_const_none;
    
    mp_obj_t lookup_list = args[8];
    size_t lookup_len;
    mp_obj_t *lookup_items;
    mp_obj_get_array(lookup_list, &lookup_len, &lookup_items);
    
    int16_t *lookup_ptr = NULL;
    int16_t lookup_array[256];
    
    if (lookup_len > 0) {
        for(size_t i = 0; i < lookup_len && i < 256; i++) {
            lookup_array[i] = (int16_t)get_int_from_obj(lookup_items[i]);
        }
        lookup_ptr = lookup_array;
    }
    
    int tint = mp_obj_get_int(args[9]);
    
    dl_push_draw_text(self->dl, sanitize_x(x), sanitize_y(y), &font->img, char_w, char_h, columns, text, text_len, lookup_ptr, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_draw_text_obj, 10, 10, dl_meth_push_draw_text);

static const mp_rom_map_elem_t dl_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&dl_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_clear), MP_ROM_PTR(&dl_push_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_pset), MP_ROM_PTR(&dl_push_pset_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_line), MP_ROM_PTR(&dl_push_line_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_fill_rect), MP_ROM_PTR(&dl_push_fill_rect_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_blt), MP_ROM_PTR(&dl_push_blt_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_draw_sprite), MP_ROM_PTR(&dl_push_draw_sprite_obj) },
    { MP_ROM_QSTR(MP_QSTR_push_draw_text), MP_ROM_PTR(&dl_push_draw_text_obj) },
};
static MP_DEFINE_CONST_DICT(dl_locals_dict, dl_locals_dict_table);

static MP_DEFINE_CONST_OBJ_TYPE(
    lightengine_DisplayList_type,
    MP_QSTR_DisplayList,
    MP_TYPE_FLAG_NONE,
    make_new, dl_make_new,
    locals_dict, &dl_locals_dict
);

// --- Module ---

// --- SPI DMA Native Driver ---
static spi_device_handle_t spi_disp_handle = NULL;
static int pin_dc = -1;
static volatile int pending_render_jobs; // Forward declaration
#define FULL_PIXELS (240 * 135)

static mp_obj_t mod_init_display(size_t n_args, const mp_obj_t *args) {
    int spi_host = mp_obj_get_int(args[0]); 
    int baudrate = mp_obj_get_int(args[1]);
    int mosi = mp_obj_get_int(args[2]);
    int sck = mp_obj_get_int(args[3]);
    int cs = mp_obj_get_int(args[4]);
    int dc = mp_obj_get_int(args[5]);

    // Wait for any pending renders from the PREVIOUS run to finish before touching SPI!
    // This prevents Kernel Panics if the user soft-reboots while Core 1 is actively sending DMA chunks.
    // Wait for any pending renders from the PREVIOUS run to finish before touching SPI!
    // This prevents Kernel Panics if the user soft-reboots while Core 1 is actively sending DMA chunks.
    while (__atomic_load_n(&pending_render_jobs, __ATOMIC_SEQ_CST) > 0) {
#ifdef MICROPY_EVENT_POLL_HOOK
        MICROPY_EVENT_POLL_HOOK
#endif
        taskYIELD();
    }
    
    pin_dc = dc;

// No DMA allocation here, done in send_display_internal

    spi_bus_config_t buscfg = {
        .miso_io_num = -1,
        .mosi_io_num = mosi,
        .sclk_io_num = sck,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = FULL_PIXELS * 2 + 8
    };

    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = baudrate,
        .mode = 0,
        .spics_io_num = cs,
        .queue_size = 7,
        .flags = SPI_DEVICE_NO_DUMMY,
    };

    spi_host_device_t host = (spi_host == 1) ? SPI2_HOST : SPI3_HOST;
    
    esp_err_t ret = spi_bus_initialize(host, &buscfg, SPI_DMA_CH_AUTO);
    if (ret != ESP_OK && ret != ESP_ERR_INVALID_STATE) {
        mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to initialize SPI bus: %d"), ret);
    }

    if (spi_disp_handle != NULL) {
        spi_bus_remove_device(spi_disp_handle);
        spi_disp_handle = NULL;
    }

    ret = spi_bus_add_device(host, &devcfg, &spi_disp_handle);
    if (ret != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("Failed to add SPI device: %d"), ret);
    }

    gpio_set_direction((gpio_num_t)dc, GPIO_MODE_OUTPUT);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mod_init_display_obj, 6, 6, mod_init_display);

static mp_obj_t mod_spi_write_cmd(mp_obj_t cmd_in) {
    uint8_t cmd = (uint8_t)mp_obj_get_int(cmd_in);
    if (spi_disp_handle == NULL) return mp_const_none;
    gpio_set_level((gpio_num_t)pin_dc, 0); 
    spi_transaction_t t;
    memset(&t, 0, sizeof(t));
    t.flags = SPI_TRANS_USE_TXDATA;
    t.length = 8;
    t.tx_data[0] = cmd;
    esp_err_t err = spi_device_transmit(spi_disp_handle, &t);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SPI cmd error: %d"), err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(mod_spi_write_cmd_obj, mod_spi_write_cmd);

static mp_obj_t mod_spi_write_data(mp_obj_t data_in) {
    if (spi_disp_handle == NULL) return mp_const_none;
    mp_buffer_info_t data_buf;
    mp_get_buffer_raise(data_in, &data_buf, MP_BUFFER_READ);
    
    gpio_set_level((gpio_num_t)pin_dc, 1);
    spi_transaction_t t;
    memset(&t, 0, sizeof(t));
    t.length = data_buf.len * 8;
    
    if (data_buf.len <= 4) {
        t.flags = SPI_TRANS_USE_TXDATA;
        memcpy(t.tx_data, data_buf.buf, data_buf.len);
    } else {
        t.tx_buffer = data_buf.buf;
    }
    
    esp_err_t err = spi_device_transmit(spi_disp_handle, &t);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_RuntimeError, MP_ERROR_TEXT("SPI data error: %d"), err);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(mod_spi_write_data_obj, mod_spi_write_data);


// --- Render & DMA Task ---
static TaskHandle_t render_task_handle = NULL;
static QueueHandle_t render_queue = NULL;
static volatile int pending_render_jobs = 0;

typedef struct {
    lightengine_Framebuffer_obj_t *fb;
    lightengine_DisplayList_obj_t *dl;
    uint16_t *palette;
} RenderJob;

enum {
    kChunkHeight = 5,
    kNumChunks = 135 / kChunkHeight,
    kChunkPixels = 240 * kChunkHeight,
    kChunkBytes = kChunkPixels * 2
};

static uint16_t *dma_chunk_bufs[2] = {NULL, NULL};
static spi_transaction_t chunk_trans[2];

static void send_display_internal(uint8_t *src, uint16_t *pal) {
    if (spi_disp_handle == NULL) return;
    gpio_set_level((gpio_num_t)pin_dc, 1);

    if (dma_chunk_bufs[0] == NULL || dma_chunk_bufs[1] == NULL) {
        if (dma_chunk_bufs[0] == NULL) dma_chunk_bufs[0] = heap_caps_malloc(kChunkBytes, MALLOC_CAP_DMA);
        if (dma_chunk_bufs[1] == NULL) dma_chunk_bufs[1] = heap_caps_malloc(kChunkBytes, MALLOC_CAP_DMA);
        if (dma_chunk_bufs[0] == NULL || dma_chunk_bufs[1] == NULL) {
            // If either failed, don't attempt to send, or we will crash/hang SPI
            if (dma_chunk_bufs[0]) { heap_caps_free(dma_chunk_bufs[0]); dma_chunk_bufs[0] = NULL; }
            if (dma_chunk_bufs[1]) { heap_caps_free(dma_chunk_bufs[1]); dma_chunk_bufs[1] = NULL; }
            return;
        }
    }

    // Memory write (0x2C)
    spi_transaction_t t;
    gpio_set_level((gpio_num_t)pin_dc, 0);
    memset(&t, 0, sizeof(t));
    t.flags = SPI_TRANS_USE_TXDATA;
    t.length = 8;
    t.tx_data[0] = 0x2C;
    spi_device_polling_transmit(spi_disp_handle, &t);
    gpio_set_level((gpio_num_t)pin_dc, 1); // Back to data mode for DMA chunks

    int buf_idx = 0;
    int queued = 0;

    for (int chunk = 0; chunk < kNumChunks; chunk++) {
        if (queued == 2) {
            spi_transaction_t *ret_trans;
            spi_device_get_trans_result(spi_disp_handle, &ret_trans, portMAX_DELAY);
            queued--;
        }

        uint16_t *dst = dma_chunk_bufs[buf_idx];
        int src_offset = chunk * kChunkPixels;
        
        for (int p = 0; p < kChunkPixels; p++) {
            uint16_t c = pal[src[src_offset + p]];
            dst[p] = (c >> 8) | (c << 8);
        }

        memset(&chunk_trans[buf_idx], 0, sizeof(spi_transaction_t));
        chunk_trans[buf_idx].length = kChunkBytes * 8;
        chunk_trans[buf_idx].tx_buffer = dst;
        
        esp_err_t err = spi_device_queue_trans(spi_disp_handle, &chunk_trans[buf_idx], portMAX_DELAY);
        if (err == ESP_OK) {
            queued++;
        }
        buf_idx = 1 - buf_idx;
    }

    while (queued > 0) {
        spi_transaction_t *ret_trans;
        spi_device_get_trans_result(spi_disp_handle, &ret_trans, portMAX_DELAY);
        queued--;
    }
}

static void render_task(void *arg) {
    RenderJob job;
    
    while (1) {
        if (xQueueReceive(render_queue, &job, portMAX_DELAY) == pdTRUE) {
            render_display_list(&job.fb->fb, job.dl->dl);
            
            if (job.palette != NULL) {
                send_display_internal(job.fb->fb.buffer, job.palette);
            }

            __atomic_fetch_sub(&pending_render_jobs, 1, __ATOMIC_SEQ_CST);
        }
    }
}

static mp_obj_t mod_init(void) {
    if (render_task_handle == NULL) {
        render_queue = xQueueCreate(10, sizeof(RenderJob));
    extern BaseType_t xTaskCreatePinnedToCore(TaskFunction_t pxTaskCode, const char * const pcName, const uint32_t usStackDepth, void * const pvParameters, UBaseType_t uxPriority, TaskHandle_t * const pxCreatedTask, const BaseType_t xCoreID);
        xTaskCreatePinnedToCore(render_task, "render_task", 4096, NULL, 5, &render_task_handle, 1);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(mod_init_obj, mod_init);

static mp_obj_t mod_submit_and_send(mp_obj_t fb_in, mp_obj_t dl_in, mp_obj_t pal_in) {
    if (render_queue != NULL) {
        __atomic_fetch_add(&pending_render_jobs, 1, __ATOMIC_SEQ_CST);
        
        uint16_t *pal_ptr = NULL;
        if (pal_in != mp_const_none) {
            mp_buffer_info_t pal_buf;
            mp_get_buffer_raise(pal_in, &pal_buf, MP_BUFFER_READ);
            pal_ptr = (uint16_t*)pal_buf.buf;
        }

        RenderJob job = {
            .fb = MP_OBJ_TO_PTR(fb_in),
            .dl = MP_OBJ_TO_PTR(dl_in),
            .palette = pal_ptr
        };
        xQueueSend(render_queue, &job, portMAX_DELAY);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_3(mod_submit_and_send_obj, mod_submit_and_send);

static mp_obj_t mod_sync(void) {
    while (__atomic_load_n(&pending_render_jobs, __ATOMIC_SEQ_CST) > 0) {
#ifdef MICROPY_EVENT_POLL_HOOK
        MICROPY_EVENT_POLL_HOOK
#endif
        taskYIELD(); // Yield without sleeping to reduce sync latency
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(mod_sync_obj, mod_sync);

static mp_obj_t mod_malloc(mp_obj_t size_in) {
    size_t size = mp_obj_get_int(size_in);
    void *ptr = heap_caps_malloc(size, MALLOC_CAP_8BIT);
    if (!ptr) {
        mp_raise_msg(&mp_type_MemoryError, MP_ROM_QSTR(MP_QSTR_Failed_to_allocate_from_FreeRTOS_heap));
    }
    return mp_obj_new_bytearray_by_ref(size, ptr);
}
static MP_DEFINE_CONST_FUN_OBJ_1(mod_malloc_obj, mod_malloc);

static mp_obj_t mod_free(mp_obj_t buf_in) {
    mp_buffer_info_t bufinfo;
    if (mp_get_buffer(buf_in, &bufinfo, MP_BUFFER_RW)) {
        if (bufinfo.buf != NULL) {
            heap_caps_free(bufinfo.buf);
        }
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(mod_free_obj, mod_free);

static mp_obj_t mod_get_free_heap(void) {
    return mp_obj_new_int(heap_caps_get_free_size(MALLOC_CAP_8BIT));
}
static MP_DEFINE_CONST_FUN_OBJ_0(mod_get_free_heap_obj, mod_get_free_heap);

static const mp_rom_map_elem_t lightengine_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__lightengine) },
    { MP_ROM_QSTR(MP_QSTR_Image), MP_ROM_PTR(&lightengine_Image_type) },
    { MP_ROM_QSTR(MP_QSTR_Sprite), MP_ROM_PTR(&lightengine_Sprite_type) },
    { MP_ROM_QSTR(MP_QSTR_Framebuffer), MP_ROM_PTR(&lightengine_Framebuffer_type) },
    { MP_ROM_QSTR(MP_QSTR_DisplayList), MP_ROM_PTR(&lightengine_DisplayList_type) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&mod_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_submit_and_send), MP_ROM_PTR(&mod_submit_and_send_obj) },
    { MP_ROM_QSTR(MP_QSTR_sync), MP_ROM_PTR(&mod_sync_obj) },
    { MP_ROM_QSTR(MP_QSTR_init_display), MP_ROM_PTR(&mod_init_display_obj) },
    { MP_ROM_QSTR(MP_QSTR_spi_write_cmd), MP_ROM_PTR(&mod_spi_write_cmd_obj) },
    { MP_ROM_QSTR(MP_QSTR_spi_write_data), MP_ROM_PTR(&mod_spi_write_data_obj) },
    { MP_ROM_QSTR(MP_QSTR_malloc), MP_ROM_PTR(&mod_malloc_obj) },
    { MP_ROM_QSTR(MP_QSTR_free), MP_ROM_PTR(&mod_free_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_free_heap), MP_ROM_PTR(&mod_get_free_heap_obj) },
    };
static MP_DEFINE_CONST_DICT(lightengine_module_globals, lightengine_module_globals_table);

const mp_obj_module_t lightengine_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&lightengine_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__lightengine, lightengine_user_cmodule);
