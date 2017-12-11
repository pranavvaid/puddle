-- #check rational

constant drop : Type

-- do
--     write k v,
--     write k' v',
--     get v,

inductive term_ (v : Type)
| var : v → term_
| input : term_
| output : term_ → term_
| mix : term_ → term_ → term_
| bind : term_ → (v → term_) → term_

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

def term := term_ string

open term_

def mix_out : term :=
    (term_.bind (term_.input _) $
        (fun d1, term_.bind (term_.input _)  $
            (fun d2, output (mix (var d1) (var d2)))))

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
| some (v, (_, bs)) := py.stmt.seq (bs ++ [v])
end

meta def fresh_name : compiler_m string :=
    do (c, bs) ← state_t.read,
       state_t.write (c + 1, bs),
       return ("d" ++ to_string c)

meta mutual def mk_binding, compile_body, compile
with mk_binding : term → compiler_m string
| t := do stmt ← compile_body t,
          (c, bs) ← state_t.read,
          state_t.write (c, stmt :: bs),
          return "foo"
with compile_body : term → compiler_m py.stmt
| (term_.input _) := pure $ py.stmt.expr $ py.mk_call ["puddle", "input"] []
| (term_.output d) := pure $ py.stmt.expr $ py.mk_call ["puddle", "output"] []
| (term_.bind m1 m2) :=
  do v ← mk_binding m1,
     compile_body (m2 v)
| (term_.var x) := pure $ py.stmt.expr (py.expr.var x)
| (term_.mix d1 d2) := pure $ py.stmt.expr (py.expr.var "mix")
with compile : term → py.fn
| t := py.fn.mk "compiled_fn" [] (compile_body t).run

#eval (compile mix_out)
