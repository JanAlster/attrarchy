#
#  Attrarchy - Dataclass-like class attributes hierarchical system
#      Copyright (c) 2025. Jan Alster
#
#      This program is free software: you can redistribute it and/or modify
#      it under the terms of the GNU General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      This program is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU General Public License for more details.
#
#      You should have received a copy of the GNU General Public License
#      along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
This example shows the intended use of Attrarchy (very basic one).
"""

import attrarchy as aa

@aa.infuse
class Line:
    width: float = 1.
    color: str = "black"

@aa.infuse
class Square:
    default = aa.Attr(Line)
    top = aa.Attr(Line, leader=default)
    bottom = aa.Attr(Line, leader=default)
    right = aa.Attr(Line, leader=default)
    left = aa.Attr(Line, leader=default)

    def __str__(self):
        # return (",\n".join([f"{line.color(), line.width()}" for line in (self.top, self.bottom, self.right, self.top)]))
        return f"{self.top.color():-^20}\n{self.left.color():<19}|\n|{self.right.color():>19}\n{self.bottom.color():-^20}\n"

# set bottom lines of all Square to red by default
Square.bottom.color.set("red")

# create instance
r = Square()
print(r)

# set all lines default to green
Line.color.set("green")
print("default to green")
print(r)

r2 = Square()

# set top line of r2 to blue
print("after r2 instance change")
r2.top.color.set("blue")
print("r")
print(r)
print()
print("r2")
print(r2)



@aa.infuse
class Cube:
    top: Square
    bottom: Square
    left: Square
    right: Square
    front: Square
    bottom: Square

c = Cube()

