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
using_well_founded { dec_tac := tactic.admit }

inductive typed : context → term → context → type → Prop
| output : forall cx d, typed cx (term.output d) cx type.unit
| input : forall cx ty, typed cx (term.input ty) cx ty
| mix : forall cx cx' cx'' d1 d2 ty1 ty2 ty3,
    typed cx d1 cx' ty1 →
    typed cx' d2 cx'' ty2 →
    (type.mix ty1 ty2) = except.ok ty3 →
    typed cx (term.mix d1 d2) cx'' ty3

end checker
end puddle
