import .syntax

namespace puddle

open puddle.syntax

def grid := list (string × nat)

def to_quantity : type → nat := 0

inductive step : grid → term → grid → term → Prop
|

end puddle
