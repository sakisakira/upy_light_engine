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
