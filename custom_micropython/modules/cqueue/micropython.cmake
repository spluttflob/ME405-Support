add_library(usermod_cqueue INTERFACE)

file(GLOB_RECURSE CQUEUE_SOURCES ${CMAKE_CURRENT_LIST_DIR}/*.c)

target_sources(usermod_cqueue INTERFACE
    ${CQUEUE_SOURCES}
)

target_include_directories(usermod_cqueue INTERFACE
    ${CMAKE_CURRENT_LIST_DIR}
)

#target_compile_definitions(usermod_cqueue INTERFACE
    #MODULE_ULAB_ENABLED=1
#)

target_link_libraries(usermod INTERFACE usermod_cqueue)

