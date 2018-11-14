Overview
========
This is an Infinidat project.

Usage
-----
Nothing to use here.


Checking out the code
=====================
Run the following commands:

    easy_install -U infi.projector
    projector devenv build


How the build process works
===========================
Many build systems try to "understand" the environment they're in and provide the necessary compiler and linker flags
that work for that environment, check if certain libraries or header files exist or which library to use and much more.

While being very helpful to reduce the amount of code you put into the build system configuration or the amount of
knowledge required by the user to build a product it usually comes with the cost of not being able to fully tweak
how and what is being built (e.g. use libX from this path instead of the system's installed libX, add this module as a
shared object but the other module include statically, decide which symbols to export, etc.).

Since one of the major goals of this project is to be able to fully and easily customize the Python being built, making
choices for the user is fine as long as you give him or her the option to change these options, but that's not entirely
possible with Python's own build system.

So instead of trying to figure out where each library or include is found, we leave it for the user to exactly specify
the compile and link flags by configuring SCons' env, and adding lots of other variables the user can use to further
tweak the build.


Command line examples for various platforms
===========================================
Building on OSX:

```
./bin/pack BUILD_PATH=./build PYTHON_SOURCE_PATH=path/to/python XFLAGS='-g -pthread -framework CoreFoundation -framework SystemConfiguration'
```


TODOs
=====
- Platforms other than Linux (Windows, OSX) and more Linux flavours (Centos, Ubuntu, Fedora, etc.)


Python 3
========

Support for Python 3 is experimental at this stage
