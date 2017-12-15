import .except
import struct_tact

namespace puddle
namespace syntax

@[derive(decidable_eq)]
inductive type : Type
| unit

def type.mix (t1 t2 : type) : except string type :=
except.error "foo"

/- The term type representing our terms implemented
   using a locally nameless representation. -/
inductive term : Type
| var : string → term
| input : type → term
| output : term → term
| mix : term → term → term
| bind : string → type → term → term → term

namespace term

-- /-- A term is closed, i.e there are no dangling `var`s. -/
-- inductive is_closed' : term → nat → Prop
-- | var : forall n m,
--     n < m →
--     is_closed' (term.var n) m
-- | input : forall ty n, is_closed' (term.input ty) n
-- | output : forall t m,
--     is_closed' t m →
--     is_closed' (term.output t) m
-- | mix : forall n t1 t2,
--     is_closed' t1 n →
--     is_closed' t2 n →
--     is_closed' (mix t1 t2) n
-- | bind : forall x v ty body n,
--     is_closed' v n →
--     is_closed' body (n + 1) →
--     is_closed' (term.bind x ty v body) n

end term

end syntax
end puddle
