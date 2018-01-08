import ..syntax
import ..map
import .core
import .subst

namespace puddle

open puddle.syntax

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
