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
| free : string → type → term
| var : nat → term
| input : type → term
| output : term → term
| mix : term → term → term
| bind : string → type → term → term → term

namespace term

/-- A term is closed, i.e there are no dangling `var`s. -/
inductive is_closed' : term → nat → Prop
| free : forall s t n,
    is_closed' (term.free s t) n
| var : forall n m,
    n < m →
    is_closed' (term.var n) m
| input : forall ty n, is_closed' (term.input ty) n
| output : forall t m,
    is_closed' t m →
    is_closed' (term.output t) m
| mix : forall n t1 t2,
    is_closed' t1 n →
    is_closed' t2 n →
    is_closed' (mix t1 t2) n
| bind : forall x v ty body n,
    is_closed' v n →
    is_closed' body (n + 1) →
    is_closed' (term.bind x ty v body) n

def is_closed (t : term) : Prop :=
is_closed' t 0

def abstract_aux (name : string) : nat → term → term
| outer (term.free name' ty) :=
    if name = name'
    then term.var outer
    else term.free name' ty
| outer (term.var b) := term.var b
| outer (term.input ty) := (term.input ty)
| outer (term.output d) :=
  term.output (abstract_aux outer d)
| outer (term.mix d1 d2) :=
  term.mix (abstract_aux outer d1) (abstract_aux outer d2)
| outer (term.bind x ty v body) :=
  term.bind x ty (abstract_aux outer v) (abstract_aux (outer + 1) body)

def abstract (n : string) (t : term) : term :=
abstract_aux n 0 t

def instantiate_aux (image : term) : nat → term → term
| outer (term.var index) :=
    if index = outer
    then image
    else term.var index
| outer (term.free name ty) := term.free name ty
| outer (term.output d) := term.output (instantiate_aux outer d)
| outer (term.mix d1 d2) :=
  term.mix (instantiate_aux outer d1) (instantiate_aux outer d2)
| outer (term.input ty) := term.input ty
| outer (term.bind x ty v body) :=
  term.bind x ty
    (instantiate_aux outer v)
    (instantiate_aux (outer + 1) body)

def instantiate (sub : term) (target : term) : term :=
instantiate_aux sub 0 target

lemma instantiate_abstract_aux :
∀ (name : string) (t : term) (ty : type) i,
    is_closed t →
    instantiate_aux (free name ty) i (abstract_aux name i t) = t :=
begin
    intros name t, induction t; intros,
    { simp [abstract_aux, instantiate_aux],
      by_cases (name = t_a); simp * at *,
      { simp [abstract_aux, instantiate_aux],
        constructor, trivial,
      },
      { existsi type.unit, simp [instantiate_aux] }
    },
    { simp [is_closed] at a,
      cases t, cases a, cases a_a,
      cases a, cases a_a,
    },
    { simp [abstract_aux, instantiate_aux], existsi type.unit,
      trivial,
    },
    { cases a,
      cases (t_ih a_a),
      existsi _,
      simp [abstract_aux, instantiate_aux],
      rw h,
    },
    { cases a,
      cases (t_ih_a a_a),
      cases (t_ih_a_1 a_a_1),
      simp [abstract_aux, instantiate_aux],
      constructor,
      simp * at *,
      admit,
      admit,
    },
    { admit }
end

lemma instantiate_abstract :
forall name t,
  exists ty,
    term.instantiate (term.free name ty) (term.abstract name t) = t :=
begin
    intros, induction t,
    { admit },
    { simp [abstract, instantiate], },
    { admit },
end

-- lemma instantiate_abstract :
-- forall name t,
--     instantiate

end term

end syntax
end puddle
