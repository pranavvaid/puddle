namespace puddle.py

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

end puddle.py
