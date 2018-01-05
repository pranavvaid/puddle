import .syntax
import .map

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

def grid (e : ext) := map string e.ty

inductive is_value : term → Prop
| input :
    forall t, is_value (term.input t)
| var :
    forall x,
        is_value (term.var x)
| mix :
    forall t1 t2,
        is_value t1 →
        is_value t2 →
        is_value (term.mix t1 t2)

-- i think we only want this defined for things of the droplet type
def to_value {e : ext} (grd: grid e) : term → e.ty
-- FIXME we should know that the thing is in there
| (term.var x) := option.get_or_else (grd.lookup x) sorry
-- FIXME input needs to specify the properties of the thing
| (term.input ty) := sorry
-- TODO does this even make sense to have an e.ty here?
| (term.output tm) := sorry
| (term.mix tm1 tm2) := e.mix_fn (to_value tm1) (to_value tm2)
| (term.bind x ty v body) := sorry
| (term.unit) := sorry


-- -- the fn for merging def merge
-- def merge {e : ext} (v1 v2 : e.ty) : e.ty := e.

-- -- the fn for partitioning
-- def partition {e : ext} (v1 : value e) : (value e × value e) := sorry

-- -- convert a value term into a value
-- def to_value {e : ext} : term → value e := sorry

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
    forall x v ty body n grd,
        is_value v →
        to_value grd v = n →
        step grd (term.bind x ty v body) (grd.insert x n) body
| mix_left :
    forall t1 t1' t2 grd grd',
        step grd t1 grd' t1' →
        step grd (term.mix t1 t2) grd' (term.mix t1' t2)
| mix_right :
    forall t1 t2 t2' grd grd',
        step grd t2 grd' t2' →
        step grd (term.mix t1 t2) grd' (term.mix t1 t2)

end puddle
