import .syntax
import .py
import system.io

namespace puddle
namespace extraction

open syntax

/-- This module defines a compiler from our droplet language to Python, and extracts
    a set of Python functions given a call the compiler.
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
   | (term.var x) := return x
   | _ :=
     do res ← fresh_name,
        stmt ← compile_body res t,
        (c, bs) ← state_t.read,
        state_t.write (c, stmt :: bs),
        return res
   end
with compile_body : string → term → compiler_m py.stmt
| res (term.input _) := pure $ py.stmt.assign res (py.mk_call puddle.runtime.input [])
| res (term.output d) :=
    do out_drop ← mk_binding d,
       pure $ py.stmt.expr $ py.mk_call puddle.runtime.output [py.expr.var out_drop]
| res (term.bind x ty m1 m2) :=
  do v ← mk_binding m1,
     compile_body res m2
| res (term.var x) := pure $ py.stmt.assign res (py.expr.var x)
| res (term.mix d1 d2) :=
    do d1 ← mk_binding d1,
       d2 ← mk_binding d2,
       pure $ py.stmt.assign res (py.expr.call puddle.runtime.mix [py.expr.var d1, py.expr.var d2])
| res (term.unit) := pure py.stmt.empty
with compile : name → term → py.fn
| n t := py.fn.mk (to_string n) [] (do n ← fresh_name, compile_body n t).run

meta def compile_pdef (n : name) : tactic string :=
do decl ← tactic.get_decl n,
   match decl with
   | declaration.defn _ _ ty body _ _ :=
   do tm ← tactic.eval_expr term body,
      pure $ (repr $ compile n tm)
   | _ := tactic.fail "err"
   end

meta def write_python_file [ioi : io.interface] (file : string) (data : string) : io unit :=
do handle ← io.mk_file_handle file io.mode.write,
   io.fs.write handle data.to_char_buffer,
   io.fs.close handle,
   return ()

meta def extract (file : option string := none) : tactic unit :=
    do ns ← attribute.get_instances `puddle_def,
       str ← ns.foldl (fun mstr n,
         do str ← mstr,
            str' ← compile_pdef n,
            return (str' ++ "\n\n" ++ str)) (return ""),
        match file with
        | none := tactic.trace str
        | some f := tactic.run_io (fun ioi, @write_python_file ioi f str)
        end

end extraction
end puddle

