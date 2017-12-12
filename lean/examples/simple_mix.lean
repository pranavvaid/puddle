import ..src.puddle

open pterm
open puddle.extraction

def mix_out : term :=
    (pterm.bind (pterm.input _) $
        (fun d1, pterm.bind (pterm.input _)  $
            (fun d2, output (mix (var d1) (var d2)))))

/-
    d1 = input()
    d2 = input()
    d3 = mix d1 d2
    r = output(d3)
    return r
-/

#eval (compile mix_out)
