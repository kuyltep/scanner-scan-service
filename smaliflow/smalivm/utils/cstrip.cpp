#include <Python.h>
#include <string>

// Функция для удаления пробелов слева и справа (аналог str.strip())
std::string c_strip(const std::string &s) {
    size_t start = s.find_first_not_of(" \t\n\r");
    if (start == std::string::npos) return "";  // Если строка пустая

    size_t end = s.find_last_not_of(" \t\n\r");
    return s.substr(start, end - start + 1);
}

// Python-обертка для `c_strip`
static PyObject* py_c_strip(PyObject* self, PyObject* args) {
    const char* input_str;

    if (!PyArg_ParseTuple(args, "s", &input_str)) {
        return NULL;
    }

    std::string result = c_strip(input_str);
    return PyUnicode_FromString(result.c_str());
}

// Описание функций модуля
static PyMethodDef CStripMethods[] = {
    {"strip", py_c_strip, METH_VARARGS, "Fast C++-based strip function"},
    {NULL, NULL, 0, NULL}
};

// Описание модуля
static struct PyModuleDef cstripmodule = {
    PyModuleDef_HEAD_INIT,
    "cstrip",
    NULL,
    -1,
    CStripMethods
};

// Функция инициализации модуля
PyMODINIT_FUNC PyInit_cstrip(void) {
    return PyModule_Create(&cstripmodule);
}
