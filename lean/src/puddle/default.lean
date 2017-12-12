-- #check rational

constant drop : Type

-- do
--     write k v,
--     write k' v',
--     get v,

-- term : measure -> Type
inductive type : Type
| unit

def context := list (string × type)

-- The polymoprhic term we use for implementing PHOAS
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

namespace py

def name := list string

inductive expr
| var : string → expr
| call : name → list expr → expr

mutual def expr.repr, expr.repr_map
with expr.repr : expr → string
| (expr.var s) := s
| (expr.call n args) :=
    string.join (list.intersperse "." n) ++
    "(" ++ string.join (list.intersperse "," $ expr.repr_map args) ++ ")"
with expr.repr_map : list expr → list string
| [] := []
| (e :: es) := expr.repr e :: expr.repr_map es

inductive stmt
| ifelse : expr → stmt → option stmt → stmt
| expr : expr → stmt
| assign : string → expr → stmt
| seq : list stmt → stmt
| empty : stmt

def mk_call : name → list expr → expr := expr.call

def indent (str : string) : string :=
"  " ++ str

mutual def stmt.repr_list, stmt.repr_list_map
with stmt.repr_list : stmt → list string
| stmt.empty := []
| (stmt.expr e) := [e.repr]
| (stmt.assign s e) := [s ++ " = " ++ expr.repr e]
| (stmt.seq ss) := stmt.repr_list_map ss
| (stmt.ifelse c tb fb) :=
    ["if " ++ c.repr ++ ":\n"] ++
    (stmt.repr_list tb).map indent -- ++
    -- ((stmt.repr_list fb).map indent)
with stmt.repr_list_map : list stmt → list string
| [] := []
| (s :: ss) := stmt.repr_list s ++ stmt.repr_list_map ss

def stmt.repr (s : stmt) : string :=
string.join (list.intersperse "\n" $ list.map indent $ stmt.repr_list s)

instance stmt.has_repr : has_repr stmt :=
⟨ stmt.repr ⟩

inductive fn
| mk : string → list string → stmt → fn

def fn.empty (nm : string) : fn :=
fn.mk nm [] stmt.empty

def fn.repr : fn → string
| (fn.mk n ps body) :=
    "def " ++ n ++ "():\n" ++ repr body

instance fn.has_repr : has_repr fn :=
⟨ fn.repr ⟩

end py

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


def compiler_st := (nat × list py.stmt)
def compiler_st.initial : compiler_st :=
(0, [])

def compiler_m (a : Type) : Type := state_t compiler_st option a

instance compiler_m.monad : monad compiler_m :=
begin
    intros,
    delta compiler_m,
    apply_instance,
end

def compiler_m.run (action : compiler_m py.stmt) : py.stmt :=
match action compiler_st.initial with
| none := sorry
| some (v, (_, bs)) := py.stmt.seq (bs.reverse ++ [v])
end

meta def fresh_name : compiler_m string :=
do (c, bs) ← state_t.read,
   state_t.write (c + 1, bs),
   return ("d" ++ to_string c)

namespace puddle.runtime

def input := ["puddle", "input"]
def output := ["puddle", "output"]
def mix := ["puddle", "mix"]

end puddle.runtime

meta mutual def mk_binding, compile_body, compile
with mk_binding : term → compiler_m string
| t :=
   match t with
   | (pterm.var x) := return x
   | _ :=
     do res ← fresh_name,
        stmt ← compile_body res t,
        (c, bs) ← state_t.read,
        state_t.write (c, stmt :: bs),
        return res
   end
with compile_body : string → term → compiler_m py.stmt
| res (pterm.input _) := pure $ py.stmt.assign res (py.mk_call puddle.runtime.input [])
| res (pterm.output d) :=
    do out_drop ← mk_binding d,
       pure $ py.stmt.expr $ py.mk_call puddle.runtime.output [py.expr.var out_drop]
| res (pterm.bind m1 m2) :=
  do v ← mk_binding m1,
     compile_body res (m2 v)
| res (pterm.var x) := pure $ py.stmt.assign res (py.expr.var x)
| res (pterm.mix d1 d2) :=
    do d1 ← mk_binding d1,
       d2 ← mk_binding d2,
       pure $ py.stmt.assign res (py.expr.call puddle.runtime.mix [py.expr.var d1, py.expr.var d2])
with compile : term → py.fn
| t := py.fn.mk "compiled_fn" [] (do n ← fresh_name, compile_body n t).run

#eval (compile mix_out)
