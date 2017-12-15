import ..src.puddle
import ..src.puddle.puddle_def

open puddle.extraction

pdef mix_out :=
    let d1 = input;
    let d2 = input;
    let d3 = mix(d1,d2);
    output(d3)

#eval (compile mix_out)
