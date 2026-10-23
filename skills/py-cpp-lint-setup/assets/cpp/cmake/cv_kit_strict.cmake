# Strict build settings that back cv-kit's C++ rules (.claude/rules/cpp-style.md).
#
#   include(cmake/cv_kit_strict.cmake)
#   cv_kit_strict(my_target)
#
# GCC and Clang only. Sanitizers are for host builds; do not ship them.
include_guard(GLOBAL)

option(CV_KIT_SANITIZE "Build with AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(CV_KIT_TSAN "Build with ThreadSanitizer (cannot be combined with CV_KIT_SANITIZE)" OFF)

if(CV_KIT_SANITIZE AND CV_KIT_TSAN)
  message(FATAL_ERROR "CV_KIT_SANITIZE and CV_KIT_TSAN cannot be used together")
endif()

function(cv_kit_strict target)
  if(NOT CMAKE_CXX_COMPILER_ID MATCHES "^(GNU|Clang|AppleClang)$")
    message(FATAL_ERROR "cv_kit_strict: unsupported compiler ${CMAKE_CXX_COMPILER_ID}")
  endif()
  target_compile_features(${target} PRIVATE cxx_std_20)
  set_target_properties(${target} PROPERTIES CXX_EXTENSIONS OFF)
  target_compile_options(${target} PRIVATE
    $<$<COMPILE_LANGUAGE:CXX>:
      -Wall -Wextra -Wpedantic -Werror
      -Wconversion -Wsign-conversion -Wshadow -Wold-style-cast -Wcast-align
      -Wnon-virtual-dtor -Woverloaded-virtual -Wnull-dereference
      -Wdouble-promotion -Wformat=2 -Wimplicit-fallthrough -Wundef -Wcast-qual
      -Wsuggest-override -Wzero-as-null-pointer-constant -Wdeprecated-copy-dtor
      -fno-exceptions -fno-rtti>
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:GNU>>:
      -Wduplicated-cond -Wlogical-op -Wuseless-cast -Wcast-align=strict>
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:Clang,AppleClang>>:
      -Wctad-maybe-unsupported>)
  # Bounds-checked operator[] and iterator checks in libstdc++ debug builds.
  target_compile_definitions(${target} PRIVATE $<$<CONFIG:Debug>:_GLIBCXX_ASSERTIONS>)
  if(CV_KIT_SANITIZE)
    target_compile_options(${target} PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer
                                             -fno-sanitize-recover=all)
    target_link_options(${target} PRIVATE -fsanitize=address,undefined)
  elseif(CV_KIT_TSAN)
    target_compile_options(${target} PRIVATE -fsanitize=thread -fno-omit-frame-pointer)
    target_link_options(${target} PRIVATE -fsanitize=thread)
  endif()
endfunction()
