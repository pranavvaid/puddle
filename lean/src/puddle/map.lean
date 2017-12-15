namespace puddle

def map (k v : Type) := list (k × v)

namespace map

def empty {k v : Type} : map k v :=
@list.nil (k × v)

def lookup {k v : Type} : map k v → k → option v
| cx k := none

def insert {k v : Type} : map k v → k → v → map k v
| cx k v := cx

def remove {k v : Type} : map k v → k → map k v
| cx k := cx

def extend {k v : Type} : map k v → map k v → map k v
| cx cx' := cx

def shrink {k v : Type} : map k v → list k → map k v
| cx keys := cx

def contains {k v : Type} : map k v → k → bool
| cx key := ff

end map

end puddle
