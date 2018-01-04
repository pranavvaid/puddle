import struct_tact
import .syntax
import .except
import .map

namespace puddle
namespace checker

open puddle.syntax

def context := map string type × list string

def context.is_empty : context → bool
| (m, _) := m = []

def context.initial : context := (map.empty, [])

def in_scope : context → string → bool
| (m, ns) n := m.contains n ∨ ns.mem n

def context.lookup : context → string → option type
| (m, _) key := m.lookup key

def context.extend : context → list (string × type) → context
| (m, ns) kvs := (m.extend kvs, ns)

def context.consume : context → string → context
| cx k := cx

def err := string

mutual def check, infer
with check : context → term → type → except err type
| cx t expected :=
    do t ← infer cx t,
       if t = expected
       then except.ok t
       else except.error "mismatch"
with infer : context → term → except err type
| cx (term.var x) := except.error "can't type var"
| cx (term.bind x ty v body) :=
   do ty' ← check cx v ty, -- we might need the normalized type here
      -- term.instantiate (term.free x ty') body)
      infer cx body
| cx (term.input t) := except.ok t
| cx (term.mix d1 d2) :=
do t1 ← infer cx d1,
   t2 ← infer cx d2,
   type.mix t1 t2
| cx (term.output d) := except.ok type.unit
| cx term.unit := except.ok type.unit
using_well_founded { dec_tac := tactic.admit }

inductive typed : context → term → context → type → Prop
| output :
    forall cx d,
    typed cx (term.output d) cx type.unit
| input :
    forall cx ty,
    typed cx (term.input ty) cx ty
| mix : forall cx cx' cx'' d1 d2 ty1 ty2 ty3,
    typed cx d1 cx' ty1 →
    typed cx' d2 cx'' ty2 →
    (type.mix ty1 ty2) = except.ok ty3 →
    typed cx (term.mix d1 d2) cx'' ty3
| var :
    forall (cx : context) x ty,
    cx.lookup x = some ty →
    typed cx (term.var x) (cx.consume x) ty
| bind :
    forall (cx cx' cx'' : context) x ty v body body_ty,
    typed cx v cx' ty →
    typed (cx'.extend [(x, ty)]) body cx'' body_ty →
    typed cx (term.bind x ty v body) cx'' body_ty
| unit : forall cx, typed cx term.unit cx type.unit

/-- A term is well-typed if we can type it in the empty context
    and the final context is empty, i.e we have consumed all bindings. -/
def well_typed (t : term) (ty : type) :=
forall final_ctx,
    context.is_empty final_ctx →
    typed context.initial t final_ctx ty

theorem check_correct :
forall t ty,
  check context.initial t ty = except.ok ty →
  well_typed t ty :=
begin
    intros,
    admit
end

end checker
end puddle
