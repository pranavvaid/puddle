import struct_tact
import .syntax
import .except

namespace puddle
namespace checker

open puddle.syntax

def context := list (string × type)
def context.empty : context := []

def context.lookup : context → string → option type
| cx k := none

def context.extend : context → context → context
| cx cx' := cx

-- #check well_founded_tactics.dec_tac

def err := string

mutual def check, infer
with check : term → type → except err type
| t expected :=
    do t ← infer t,
       if t = expected
       then except.ok t
       else except.error "mismatch"
with infer : term → except err type
| (term.free x ty) := except.ok ty
| (term.var x) := except.error "can't type var"
| (term.bind x ty v body) :=
   do ty' ← check v ty, -- we might need the normalized type here
      infer (term.instantiate (term.free x ty') body)
| (term.input t) := except.ok t
| (term.mix d1 d2) :=
do t1 ← infer d1,
   t2 ← infer d2,
   type.mix t1 t2
| (term.output d) := except.ok type.unit
using_well_founded { dec_tac := tactic.admit }

inductive typed : term → type → Prop
| output : forall d, typed (term.output d) type.unit
| input : forall ty, typed (term.input ty) ty
| mix : forall d1 d2 ty1 ty2 ty3,
    typed d1 ty1 →
    typed d2 ty2 →
    (type.mix ty1 ty2) = except.ok ty3 →
    typed (term.mix d1 d2) ty3
| free : forall x ty,
    typed (term.free x ty) ty

end checker
end puddle
