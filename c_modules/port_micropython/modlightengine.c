#include "py/runtime.h"
#include "py/obj.h"
#include "engine_types.h"
#include "engine_render.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"

// --- Image Type ---
typedef struct _lightengine_Image_obj_t {
    mp_obj_base_t base;
    EngineImage img;
} lightengine_Image_obj_t;


static mp_obj_t image_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    mp_arg_check_num(n_args, n_kw, 3, 3, false);
    lightengine_Image_obj_t *self = m_new_obj(lightengine_Image_obj_t);
    self->base.type = type;
    self->img.width = mp_obj_get_int(args[0]);
    self->img.height = mp_obj_get_int(args[1]);
    self->img.format = mp_obj_get_int(args[2]);
    
    size_t size = self->img.width * self->img.height;
    if (self->img.format == kFormatArgb4444) size *= 2;
    self->img.data = m_new(uint8_t, size);
    
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
    mp_arg_check_num(n_args, n_kw, 3, 3, false);
    lightengine_Framebuffer_obj_t *self = m_new_obj(lightengine_Framebuffer_obj_t);
    self->base.type = type;
    self->fb.width = mp_obj_get_int(args[0]);
    self->fb.height = mp_obj_get_int(args[1]);
    self->fb.format = mp_obj_get_int(args[2]);
    
    size_t size = self->fb.width * self->fb.height;
    if (self->fb.format == kFormatArgb4444) size *= 2;
    self->fb.buffer = m_new(uint8_t, size);
    
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
    self->dl = dl_create();
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
    dl_push_pset(self->dl, mp_obj_get_int(args[1]), mp_obj_get_int(args[2]), mp_obj_get_int(args[3]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_pset_obj, 4, 4, dl_meth_push_pset);

static mp_obj_t dl_meth_push_line(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    dl_push_line(self->dl, mp_obj_get_int(args[1]), mp_obj_get_int(args[2]), mp_obj_get_int(args[3]), mp_obj_get_int(args[4]), mp_obj_get_int(args[5]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_line_obj, 6, 6, dl_meth_push_line);

static mp_obj_t dl_meth_push_fill_rect(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    dl_push_fill_rect(self->dl, mp_obj_get_int(args[1]), mp_obj_get_int(args[2]), mp_obj_get_int(args[3]), mp_obj_get_int(args[4]), mp_obj_get_int(args[5]));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_fill_rect_obj, 6, 6, dl_meth_push_fill_rect);

static mp_obj_t dl_meth_push_draw_sprite(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int cx = mp_obj_get_int(args[1]);
    int cy = mp_obj_get_int(args[2]);
    float scale = mp_obj_get_float(args[3]);
    lightengine_Sprite_obj_t *sprite = MP_OBJ_TO_PTR(args[4]);
    int tint = mp_obj_get_int(args[5]);
    
    dl_push_draw_sprite(self->dl, cx, cy, scale, &sprite->sprite, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_draw_sprite_obj, 6, 6, dl_meth_push_draw_sprite);

static mp_obj_t dl_meth_push_blt(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int x = mp_obj_get_int(args[1]);
    int y = mp_obj_get_int(args[2]);
    lightengine_Image_obj_t *img = MP_OBJ_TO_PTR(args[3]);
    int u = mp_obj_get_int(args[4]);
    int v = mp_obj_get_int(args[5]);
    int w = mp_obj_get_int(args[6]);
    int h = mp_obj_get_int(args[7]);
    int colkey = mp_obj_get_int(args[8]);
    int tint = mp_obj_get_int(args[9]);
    
    dl_push_blt(self->dl, x, y, &img->img, u, v, w, h, colkey, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_blt_obj, 10, 10, dl_meth_push_blt);

static mp_obj_t dl_meth_push_draw_text(size_t n_args, const mp_obj_t *args) {
    lightengine_DisplayList_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    int x = mp_obj_get_int(args[1]);
    int y = mp_obj_get_int(args[2]);
    lightengine_Image_obj_t *font = MP_OBJ_TO_PTR(args[3]);
    int char_w = mp_obj_get_int(args[4]);
    int char_h = mp_obj_get_int(args[5]);
    int columns = mp_obj_get_int(args[6]);
    
    mp_buffer_info_t text_bufinfo;
    mp_get_buffer_raise(args[7], &text_bufinfo, MP_BUFFER_READ);
    const uint8_t *text = text_bufinfo.buf;
    int text_len = text_bufinfo.len;
    
    int16_t *lookup = NULL;
    int tint = mp_obj_get_int(args[8]);
    
    dl_push_draw_text(self->dl, x, y, &font->img, char_w, char_h, columns, text, text_len, lookup, tint);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(dl_push_draw_text_obj, 9, 9, dl_meth_push_draw_text);

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

static TaskHandle_t render_task_handle = NULL;
static QueueHandle_t render_queue = NULL;

typedef struct {
    lightengine_Framebuffer_obj_t *fb;
    lightengine_DisplayList_obj_t *dl;
} RenderJob;

static void render_task(void *arg) {
    RenderJob job;
    while (1) {
        if (xQueueReceive(render_queue, &job, portMAX_DELAY) == pdTRUE) {
            render_display_list(&job.fb->fb, job.dl->dl);
        }
    }
}

static mp_obj_t mod_init(void) {
    if (render_task_handle == NULL) {
        render_queue = xQueueCreate(10, sizeof(RenderJob));
        xTaskCreate(render_task, "render_task", 4096, NULL, 5, &render_task_handle);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(mod_init_obj, mod_init);

static mp_obj_t mod_submit_display_list(mp_obj_t fb_in, mp_obj_t dl_in) {
    if (render_queue == NULL) return mp_const_none;
    
    RenderJob job = {
        .fb = MP_OBJ_TO_PTR(fb_in),
        .dl = MP_OBJ_TO_PTR(dl_in)
    };
    xQueueSend(render_queue, &job, portMAX_DELAY);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(mod_submit_display_list_obj, mod_submit_display_list);

static const mp_rom_map_elem_t lightengine_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR__lightengine) },
    { MP_ROM_QSTR(MP_QSTR_Image), MP_ROM_PTR(&lightengine_Image_type) },
    { MP_ROM_QSTR(MP_QSTR_Sprite), MP_ROM_PTR(&lightengine_Sprite_type) },
    { MP_ROM_QSTR(MP_QSTR_Framebuffer), MP_ROM_PTR(&lightengine_Framebuffer_type) },
    { MP_ROM_QSTR(MP_QSTR_DisplayList), MP_ROM_PTR(&lightengine_DisplayList_type) },
    { MP_ROM_QSTR(MP_QSTR_init), MP_ROM_PTR(&mod_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_submit_display_list), MP_ROM_PTR(&mod_submit_display_list_obj) },
};
static MP_DEFINE_CONST_DICT(lightengine_module_globals, lightengine_module_globals_table);

const mp_obj_module_t lightengine_user_cmodule = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&lightengine_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR__lightengine, lightengine_user_cmodule);
