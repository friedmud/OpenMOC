%module openmoc_cuda

%{
    #define SWIG_FILE_WITH_INIT
    #include "../src/dev/DeviceMaterial.h"
    #include "../src/dev/DeviceFlatSourceRegion.h"
    #include "../src/dev/DeviceTrack.h"
    #include "../src/dev/DeviceQuery.h"

    /* Exception helpers */
    static int swig_c_error_num = 0;
    static char swig_c_err_msg[512];

    const char* err_occurred(void) {
        if (swig_c_error_num) {
            swig_c_error_num = 0;
            return (const char*)swig_c_err_msg;
        }
        return NULL;
    }

    void set_err(const char *msg) {
        swig_c_error_num = 1;
        strncpy(swig_c_err_msg, msg, 256);
    }
%}


%exception {
    try {
        $function
    } catch (const std::runtime_error &e) {
        SWIG_exception(SWIG_RuntimeError, err_occurred());
        return NULL;
    } catch (const std::exception &e) {
        SWIG_exception(SWIG_RuntimeError, e.what()); 
    }
}


%include "../numpy.i"


%init %{
     import_array();
%}

%include <exception.i> 
%include ../src/dev/DeviceMaterial.h
%include ../src/dev/DeviceFlatSourceRegion.h
%include ../src/dev/DeviceTrack.h
%include ../src/dev/DeviceQuery.h

typedef float FP_PRECISION;
