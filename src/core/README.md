# building the vision stuff

You'll need `pkg-config` and `opencv` version at least 2.4.9.
On Debian and (probably) Ubuntu, this is in package `libopencv-dev`.

The build script (`build.rs`) is run when `cargo` builds everything.
It uses `pkg-config` to find the `opencv` libraries, and then calls a C compiler
to build the C++ code. You must list the C++ files you want to compile in there.
This build a static library that will then be linked with the puddle library.

In the puddle library, you should then wrap the unsafe C functions, then you can
call than. See the `src/vision/opencv_hello.cpp` for the example opencv code.
It's wrapped in `src/vision/mod.rs`, the module declaration. Then the
`src/bin/hello.rs` binary calls the wrapped function to actually do something.
Calling `cargo run --bin hello` should "just work".
