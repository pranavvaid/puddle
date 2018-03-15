// build.rs

extern crate cc;
extern crate pkg_config;


fn main() {
    pkg_config::Config::new()
        .statik(true)
        .atleast_version("2.4.9").probe("opencv").unwrap();

    cc::Build::new()
        .cpp(true)
        .file("src/vision/opencv_hello.cpp")
        .compile("vision");
}
