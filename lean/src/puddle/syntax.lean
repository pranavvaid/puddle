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
| unit : term

namespace term

meta instance reflect : has_reflect term
| (term.var x) := `(term.var x)
| (term.input t) := `(λ t, term.input t).subst (t.reflect)
| (term.output tm) := `(λ tm, term.output tm).subst (reflect tm)
| (term.mix tm1 tm2) := (`(λ tm1, λ tm2, term.mix tm1 tm2).subst (reflect tm1)).subst (reflect tm2)
| (term.bind x ty v body) :=
    ((`(λ v, λ ty, λ body, term.bind x ty v body).subst (reflect v)).subst (ty.reflect)).subst (reflect body)
| (term.unit) := `(term.unit)

def repr : term → string
| (term.var x) := "term.var " ++ to_string x
| (term.input t) := "term.input " ++ t.repr
| (term.output tm) := "term.output " ++ tm.repr
| (term.mix tm1 tm2) := "term.mix " ++ tm1.repr ++ tm2.repr
| (term.bind x ty v body) := "term.bind " ++ x ++ ty.repr ++ v.repr ++ body.repr
| (term.unit) := "term.unit"

end term

end syntax
end puddle
