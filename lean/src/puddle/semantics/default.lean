import ..syntax
import ..map

namespace puddle

open puddle.syntax

structure ext :=
    (ty : Type)
    -- (default : ty)
    (mix_fn : ty → ty → ty)
    (split_fn : ty → (ty × ty))

def ext.empty : ext :=
{ ty := unit, mix_fn := fun u1 u2, (), split_fn := fun _, ((), ()) }

/- given a list of *independent* extensions, return one that deals with the
   product of the extension types -/
def multi_ext : list ext → ext
| [] := ext.empty
| (⟨e_ty, e_mix_fn, e_split_fn⟩ :: es) :=
  let ⟨ms_ty, ms_mix_fn, ms_split_fn⟩ := multi_ext es
  in {
    ty := e_ty × ms_ty,
    mix_fn := λ v1 v2,
      (e_mix_fn v1.fst v2.fst,
       ms_mix_fn v1.snd v2.snd),
    split_fn := λ v1,
      let (e1, e2) := e_split_fn v1.fst,
          (ms1, ms2) := ms_split_fn v1.snd
      in ((e1, ms1), (e2, ms2))
  }

@[reducible] def quantity : Type := ℕ -- Should be Real

inductive value (e : ext)
| val : quantity → e.ty → value
| pair : value → value → value

def grid (e : ext) := map string (value e)

def grid.input {e : ext} (g : grid e) (t : type) : option (string × grid e) := none

inductive is_value : term → Prop
| loc :
    forall l,
        is_value (term.location l)
| var :
    forall x,
        is_value (term.var x)
| mix :
    forall t1 t2,
        is_value t1 →
        is_value t2 →
        is_value (term.mix t1 t2)

def ext.mix (e : ext) : value e → value e → option (value e)
| (value.val q1 e1) (value.val q2 e2) :=
    value.val (q1 + q2) (e.mix_fn e1 e2)
| _ _ := none

def ext.split (e : ext) (v1 : value e) : option (value e) := none

def grid.to_value {e : ext} (grd: grid e) : term → option (value e)
| (term.location l) := none -- this should be only success case
| _ := none

-- TODO: Fill me in
inductive is_subst : term → term → term → Prop

inductive step (e : ext) : grid e → term → grid e → term → Prop
| output :
    forall grd grd' t t',
        step grd t grd' t' →
        step grd (term.output t) grd' (term.output t')
| output_value :
    forall grd t,
        step grd (term.output t) grd term.unit
| bind_binding :
    forall x v v' ty body grd grd',
        step grd v grd' v' →
        step grd (term.bind x ty v body) grd' (term.bind x ty v' body)
| bind_value :
    forall x v ty body body' grd,
        is_value v →
        is_subst body v body'→
        step grd (term.bind x ty v body) grd body'
| mix_left :
    forall t1 t1' t2 grd grd',
        step grd t1 grd' t1' →
        step grd (term.mix t1 t2) grd' (term.mix t1' t2)
| mix_right :
    forall t1 t2 t2' grd grd',
        step grd t2 grd' t2' →
        step grd (term.mix t1 t2) grd' (term.mix t1 t2)
| input :
    forall grd ty loc grd',
        grid.input grd ty = some (loc, grd') →
        step grd (term.input ty) grd' (term.location loc)

end puddle
