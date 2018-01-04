import ..src.puddle
import ..src.puddle.puddle_def

open puddle.extraction

pdef mix_out :=
    let d1 = input;
    let d2 = input;
    let d3 = mix d1 d2;
    output d3;

pdef in_out :=
    let d1 = input;
    output d1;

run_cmd extract -- this one just prints the python code
run_cmd (extract "examples/simple_mix.py") -- this one generates a file
