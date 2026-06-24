add_library(usermod_sound_engine INTERFACE)

target_sources(usermod_sound_engine INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}/sound_engine.c
)

target_include_directories(usermod_sound_engine INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

target_link_libraries(usermod INTERFACE usermod_sound_engine)
