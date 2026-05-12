function(gpwbpp_enable_warnings target)
  if(MSVC)
    target_compile_options(${target} PRIVATE $<$<COMPILE_LANGUAGE:CXX>:/W4>)
  else()
    target_compile_options(
      ${target}
      PRIVATE
        $<$<COMPILE_LANGUAGE:CXX>:-Wall>
        $<$<COMPILE_LANGUAGE:CXX>:-Wextra>
        $<$<COMPILE_LANGUAGE:CXX>:-Wpedantic>
    )
  endif()
endfunction()
