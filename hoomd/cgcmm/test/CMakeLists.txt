# Maintainer: joaander

###############################
# need a few settings for the unit test library
# first, they need the boost unit test framework added as a library
set(ADDITIONAL_LIBS _hoomd
        _cgcmm
        _md
        ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY}
        )

# boost 1.60.0 requires the boost timer and chrono be linked to unit tests
if (Boost_MINOR_VERSION GREATER 59)
list(APPEND ADDITIONAL_LIBS ${Boost_TIMER_LIBRARY} ${Boost_CHRONO_LIBRARY} ${Boost_SYSTEM_LIBRARY})
endif ()

# then we need to specify BOOST_TEST_DYN_LINK if the unit test framework library is a shared lib
if("${Boost_UNIT_TEST_FRAMEWORK_LIBRARY}" MATCHES "\\.dylib$")
add_definitions(-DBOOST_TEST_DYN_LINK)
endif("${Boost_UNIT_TEST_FRAMEWORK_LIBRARY}" MATCHES "\\.dylib$")

if("${Boost_UNIT_TEST_FRAMEWORK_LIBRARY}" MATCHES "\\.so$")
add_definitions(-DBOOST_TEST_DYN_LINK)
endif("${Boost_UNIT_TEST_FRAMEWORK_LIBRARY}" MATCHES "\\.so$")

enable_testing()

###################################
## Setup all of the test executables in a for loop
set(TEST_LIST
    test_cgcmm_angle_force
    test_cgcmm_force
    )

foreach (CUR_TEST ${TEST_LIST} ${MPI_TEST_LIST})
    # Need to define NO_IMPORT_ARRAY in every file but hoomd_module.cc
    set_source_files_properties(${CUR_TEST}.cc PROPERTIES COMPILE_DEFINITIONS NO_IMPORT_ARRAY)

    # add and link the unit test executable
    if(ENABLE_CUDA AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${CUR_TEST}.cu)
    cuda_add_executable(${CUR_TEST} EXCLUDE_FROM_ALL ${CUR_TEST}.cc
            ${CMAKE_CURRENT_SOURCE_DIR}/${CUR_TEST}.cu OPTIONS
            ${CUDA_ADDITIONAL_OPTIONS})
    else(ENABLE_CUDA AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${CUR_TEST}.cu)
    add_executable(${CUR_TEST} EXCLUDE_FROM_ALL ${CUR_TEST}.cc)
    endif(ENABLE_CUDA AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${CUR_TEST}.cu)

    add_dependencies(test_all ${CUR_TEST})

    target_link_libraries(${CUR_TEST} ${ADDITIONAL_LIBS} ${HOOMD_COMMON_LIBS})
    fix_cudart_rpath(${CUR_TEST})

    if (ENABLE_MPI)
        # set appropriate compiler/linker flags
        if(MPI_COMPILE_FLAGS)
            set_target_properties(${CUR_TEST} PROPERTIES COMPILE_FLAGS "${MPI_COMPILE_FLAGS}")
        endif(MPI_COMPILE_FLAGS)
        if(MPI_LINK_FLAGS)
            set_target_properties(${CUR_TEST} PROPERTIES LINK_FLAGS "${MPI_LINK_FLAGS}")
        endif(MPI_LINK_FLAGS)
    endif (ENABLE_MPI)
endforeach (CUR_TEST)

# add non-MPI tests to test list first
foreach (CUR_TEST ${TEST_LIST})
    # add it to the unit test list
    get_target_property(CUR_TEST_EXE ${CUR_TEST} LOCATION)

    if (ENABLE_MPI)
        add_test(${CUR_TEST} ${MPIEXEC} ${MPIEXEC_NUMPROC_FLAG} 1 ${MPIEXEC_POSTFLAGS} ${CUR_TEST_EXE})
    else()
        add_test(${CUR_TEST} ${CUR_TEST_EXE})
    endif()
endforeach(CUR_TEST)

# add MPI tests
foreach (CUR_TEST ${MPI_TEST_LIST})
    # add it to the unit test list
    get_target_property(CUR_TEST_EXE ${CUR_TEST} LOCATION)

    # add mpi- prefix to distinguish these tests
    set(MPI_TEST_NAME mpi-${CUR_TEST})

    add_test(${MPI_TEST_NAME}
             ${MPIEXEC} ${MPIEXEC_NUMPROC_FLAG}
             ${NProc_${CUR_TEST}} ${MPIEXEC_POSTFLAGS}
             ${CUR_TEST_EXE})
endforeach(CUR_TEST)