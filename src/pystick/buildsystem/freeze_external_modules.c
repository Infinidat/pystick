#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif

PyDoc_STRVAR(module_doc, "This module exposes Pythonic API to set _Py_PackageContext for non-builtin frozen extensions.");

static PyObject* package_context_str = NULL;

static PyObject*
get_py_package_context(PyObject* self, PyObject* args) {
	if (_Py_PackageContext == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	} else {
		return PyString_FromString(_Py_PackageContext);
	}
}

static PyObject*
set_py_package_context(PyObject* self, PyObject* args) {
	char* str;
	if (!PyArg_ParseTuple(args, "z:set_py_package_context", &str)) {
		return NULL;
	}

	if (package_context_str != NULL) {
		free(package_context_str);
		package_context_str = NULL;
	}

	if (str == NULL) {
		_Py_PackageContext = NULL;
	} else {
		package_context_str = strdup(str);
		if (package_context_str == NULL) {
	        return PyErr_NoMemory();
		}
		_Py_PackageContext = package_context_str;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef freeze_external_modules_methods[] = {
    {"get_py_package_context", get_py_package_context, METH_NOARGS },
    {"set_py_package_context", set_py_package_context, METH_VARARGS },
    { NULL, NULL } /* Sentinel */
};

PyMODINIT_FUNC
initfreeze_external_modules(void) {
   	Py_InitModule3("freeze_external_modules", freeze_external_modules_methods, module_doc);
}

#ifdef __cplusplus
}
#endif