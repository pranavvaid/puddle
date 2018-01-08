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

inductive droplet (e : ext)
| val : quantity → e.ty → droplet

def ext.mix (e : ext) : droplet e → droplet e → option (droplet e)
| (droplet.val q1 e1) (droplet.val q2 e2) :=
    droplet.val (q1 + q2) (e.mix_fn e1 e2)
| _ _ := none

def ext.split (e : ext) (v1 : droplet e) : option (droplet e) := none

def grid (e : ext) := map string (droplet e)

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

def grid.to_droplet {e : ext} (grd: grid e) : term → option (droplet e)
| (term.location l) := none -- this should be only success case
| _ := none

def grid.input {e : ext} (g : grid e) (t : type) : option (string × grid e) := none

def grid.mix {e : ext} (g : grid e) (v1 v2 : droplet e) : option (string × grid e) := none

end puddle
