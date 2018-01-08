import ..syntax
import ..map
import .core
import .subst

namespace puddle

open puddle.syntax

inductive step (e : ext) : grid e → term → grid e → term → Prop
/- Output -/
| output :
    forall grd grd' t t',
        step grd t grd' t' →
        step grd (term.output t) grd' (term.output t')
| output_value :
    forall grd t,
        step grd (term.output t) grd term.unit
/- Let bindings -/
| bind_binding :
    forall x v v' ty body grd grd',
        step grd v grd' v' →
        step grd (term.bind x ty v body) grd' (term.bind x ty v' body)
| bind_value :
    forall x v ty body body' grd,
        is_value v →
        is_subst body v body'→
        step grd (term.bind x ty v body) grd body'
/- Mix -/
| mix_left :
    forall t1 t1' t2 grd grd',
        step grd t1 grd' t1' →
        step grd (term.mix t1 t2) grd' (term.mix t1' t2)
| mix_right :
    forall t1 t2 t2' grd grd',
        step grd t2 grd' t2' →
        step grd (term.mix t1 t2) grd' (term.mix t1 t2)
| mix_value :
    forall t1 t2 v1 v2 loc (grd grd' : grid e),
        is_value t1 →
        is_value t2 →
        grid.to_droplet grd t1 = some v1 →
        grid.to_droplet grd t2 = some v2 →
        grid.mix grd v1 v2 = some (loc, grd') →
        step grd (term.mix t1 t2) grd' (term.location loc)
/- Split -/
| split_step :
    forall grd t1 t2 grd',
        step grd t1 grd' t2 →
        step grd (term.split t1) grd' (term.split t2)
| split_value :
    forall t1 d1 l1 l2 (grd grd' : grid e),
        is_value t1 →
        grid.to_droplet grd t1 = some d1 →
        grid.split grd d1 = some (l1, l2, grd') →
        step grd (term.split t1) grd' (term.mk_pair (term.location l1) (term.location l2))
/- Tuples -/
| pair_step_left :
    forall t1 t1' t2 grd grd',
        step grd t1 grd' t1' →
        step grd (term.mk_pair t1 t2) grd' (term.mk_pair t1' t2)
| pair_step_right :
    forall t1 t2 t2' grd grd',
        step grd t2 grd' t2' →
        step grd (term.mk_pair t1 t2) grd' (term.mk_pair t1 t2')
/- Input -/
| input :
    forall grd ty loc grd',
        grid.input grd ty = some (loc, grd') →
        step grd (term.input ty) grd' (term.location loc)

end puddle
