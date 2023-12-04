# pitch

Pitch is a low-level programming language with high-ish-level abstractions that compiles to C.

**Goals**

- [ ] Simplicity
- [ ] Modular type system
- [ ] Simple and safe memory management
- [ ] (At least partial) interoperability with C

## Values and copying

```
struct Point {
    x: i32;
    y: i32;
}

fn add_one(point: ref Point) {
    point->x += 1;
}

fn main() i32 {
    let x = Point { x: 1, y: 2 };
    add_one(&x);
}
```
