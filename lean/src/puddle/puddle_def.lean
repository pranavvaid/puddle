
import .syntax

#check tactic.coinduction

namespace puddle
namespace puddle_def

open lean.parser
open interactive
open syntax

meta def puddle_body : lean.parser term := sorry

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
   return ().

end puddle_def
end puddle

pdef try_mix :=

