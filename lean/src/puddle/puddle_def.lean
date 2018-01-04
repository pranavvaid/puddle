
import .syntax

#check tactic.coinduction

namespace puddle
namespace puddle_def

open lean.parser
open interactive
open syntax


@[user_attribute] meta def puddle_def_attr : user_attribute unit :=
{ name := `puddle_def, descr := "Mark as a Puddle definition" }

meta def puddle_body : lean.parser term :=
(do tk "let",
    x ← ident,
    tk "=",
    fn ← ident,
    val ← (if fn = `input
    then return $ term.input type.unit
    else if fn = `output
    then return $ (term.output term.unit)
    else if fn = `mix
    then do d1 ← ident, d2 ← ident,
            let tm := term.mix (term.var (to_string d1)) (term.var (to_string d2)),
            pure tm
    else (tactic.fail "foo" : tactic term)),
    tk ";",
    obody ← optional puddle_body,
    match obody with
    | none := return (term.bind (to_string x) type.unit val term.unit)
    | some body := return (term.bind (to_string x) type.unit val body)
    end) <|>
(do x ← ident,
    if x = `output
    then do arg ← ident,
            let tm := term.output (term.var (to_string arg)),
            tk ";",
            pure tm
    else (tactic.fail "expected output found:" : tactic term))

--   decl ← inductive_decl.parse meta_info,
--   add_coinductive_predicate decl.u_names decl.params $ decl.decls.map $ λ d, (d.sig, d.intros),
--   decl.decls.mmap' $ λ d, do {
--     get_env >>= λ env, set_env $ env.add_namespace d.name,
--     meta_info.attrs.apply d.name,
--     d.attrs.apply d.name,
--     some doc_string ← pure meta_info.doc_string | skip,
--     add_doc_string d.name doc_string
--   }

@[user_command]
meta def puddle_def (meta_info : decl_meta_info) (_ : parse $ tk "pdef") : lean.parser unit :=
do i ← ident,
   tk ":=",
   tm ← puddle_body,
   -- I'll show you the underlying term tactic.trace tm.repr,
   tactic.add_decl (mk_definition i [] `(term) `(tm)),
   puddle_def_attr.set i () tt,
   return ()

end puddle_def
end puddle
