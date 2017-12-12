inductive type : Type
| unit

def context := list (string × type)

/- The polymoprhic term type representing our syntax, we use
   PHOAS to implement the name binding.
-/
inductive pterm (v : Type) /- :context → type → -/ : Type
| var : v → pterm
| input : pterm
| output : pterm → pterm
| mix : pterm → pterm → pterm
| bind : pterm → (v → pterm) → pterm

-- output (if cond then d1 else d2)

-- if cond:
--   x = d1
-- else:
--   x = d2
--
-- output x

def term := pterm string

open pterm

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
