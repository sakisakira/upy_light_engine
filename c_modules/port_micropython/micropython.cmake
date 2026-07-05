add_library(usermod_lightengine INTERFACE)

target_sources(usermod_lightengine INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/modlightengine.c
    ${CMAKE_CURRENT_LIST_DIR}/../core/engine_types.c
    ${CMAKE_CURRENT_LIST_DIR}/../core/engine_render.c
)

target_include_directories(usermod_lightengine INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
    ${CMAKE_CURRENT_LIST_DIR}/../core
)

target_link_libraries(usermod INTERFACE usermod_lightengine)

# Performance optimization: force -O3 for the render pipeline to unroll loops
set_source_files_properties(
    ${CMAKE_CURRENT_LIST_DIR}/../core/engine_render.c
    PROPERTIES COMPILE_FLAGS "-O3"
)
