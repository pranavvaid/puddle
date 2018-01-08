import .except
import struct_tact

namespace puddle
namespace syntax

@[derive(decidable_eq)]
inductive type : Type
| unit

namespace type

meta def reflect : has_reflect type :=
by tactic.mk_has_reflect_instance

def mix (t1 t2 : type) : except string type :=
except.error "foo"

def repr : type → string
| _ := "type"

end type

/- The term type representing our terms implemented
   using a locally nameless representation. -/
@[derive(decidable_eq)]
inductive term : Type
| var : string → term
| input : type → term
| output : term → term
| mix : term → term → term
| bind : string → type → term → term → term
| location : string → term
| unit : term

namespace term

meta instance reflect : has_reflect term
| (term.var x) := `(term.var x)
| (term.input t) := `(λ t, term.input t).subst (t.reflect)
| (term.output tm) := `(λ tm, term.output tm).subst (reflect tm)
| (term.mix tm1 tm2) := (`(λ tm1, λ tm2, term.mix tm1 tm2).subst (reflect tm1)).subst (reflect tm2)
| (term.bind x ty v body) :=
    ((`(λ v, λ ty, λ body, term.bind x ty v body).subst (reflect v)).subst (ty.reflect)).subst (reflect body)
| (term.location l) := `(term.location l)
| (term.unit) := `(term.unit)

def repr : term → string
| (term.var x) := "term.var " ++ to_string x
| (term.input t) := "term.input " ++ t.repr
| (term.output tm) := "term.output " ++ tm.repr
| (term.mix tm1 tm2) := "term.mix " ++ tm1.repr ++ tm2.repr
| (term.bind x ty v body) := "term.bind " ++ x ++ ty.repr ++ v.repr ++ body.repr
| (term.location l) := "term.location " ++ (has_repr.repr l)
| (term.unit) := "term.unit"

instance has_repr : has_repr term :=
⟨ repr ⟩

def to_string : term → string
| (term.var x) := x
| (term.input t) := "input " ++ t.repr -- fix me
| (term.output tm) := "output " ++ tm.to_string
| (term.mix tm1 tm2) := "mix " ++ tm1.to_string ++ tm2.to_string
| (term.bind x ty v body) := -- fix me
    "let " ++ x ++ ": " ++ ty.repr ++ v.to_string ++ ";\n" ++ body.to_string
| (term.location l) := "droplet:" ++ l
| (term.unit) := "()"

instance has_to_string : has_to_string term :=
⟨ to_string ⟩

end term

end syntax
end puddle
