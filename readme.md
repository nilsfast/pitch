# pitch

Pitch is a low-level programming language with high-ish-level abstractions that compiles to C.

**Goals**

- [ ] Simplicity
- [ ] Modular type system
- [ ] Simple and safe memory management
- [ ] (At least partial) interoperability with C

# Memory safety concept

Rust is very strict about memory safety, but it's also very complicated. C is very lax with enforcing memory safety, which makes it unsafe. Pitch tries to be simpler, but still safe.

## Simple things first: Passing values

The simplest way to pass a value is to pass it directly by value. This is the one and only behaviour for primitive types like `i32`, `u32`, `f32` or `bool`.

When looking at more complex stuff, like structs, passing them by value can get really inefficient really fast. So we need a way to pass them by reference. This is where references come in.

## References

References are a way to pass a value by reference. They are similar to pointers in C, but they are not nullable. Under the hood, they are just C pointers, but the compiler makes sure that they are never null and that no arithmetic is done on them.

Let's consider this simple example struct:

```
struct Foo {
    a: i32;
    b: i32;
}
```

We can create a struct like this:

```
let foo = Foo {a: 1, b: 2};
```

When we pass this struct to a function we have to create a reference to it:

```
fn main() {
    let foo = Foo {a: 1, b: 2};
    bar(&foo); // ref foo is also valid
}
```

The `&` operator creates a reference to the value. The `bar` function has to be defined like this:

```
fn bar(foo: &Foo) {
    // ...
}
```

The `&` operator in the function signature means that the function takes a reference to a `Foo` struct.

We now have a problem on our hands: What if the `bar` function does things with the struct that we don't want it to do like setting it to `null` or retaining a reference somewhere and accessing the struct after the function returns

## Arenas (or something similar) built in

In pitch, it is possible to tie the lifetime of a value to the lifetime of a function or a block. When the function or block ends, the value is freed.

Let's look at a linked list example:

```
struct Node {
    value: i32;
    next: Maybe[&Node];
}

fn main() {
    let node = Node {value: 1, next: null};
    let node2 = Node {value: 2, next: null};
    node.next = &node2;
}
```

The nodes are automatically allocated on the heap and freed when the function ends. Lets create a function that inserts a new node:

```
fn insert(node: &Node, value: i32) {
    let new_node = Node<..>{value: value, next: null};
    node.next = &new_node;
}
```

The `<..>` annotation tells the compiler that the node is allocated on the heap and that it's lifetime is tied to the lifetime of the parent function.

If we want to control the memory more precisely, we can use named arenas:

```
fn main() {
    let nodes = Arena();
    let node = Node:nodes{value: 1, next: null};
    let node2 = Node:nodes{value: 2, next: null};
    node.next = node2;
}
```

Now we have specified that the nodes are allocated in the `nodes` arena. This means that the nodes are freed when the `nodes` variable goes out of scope.

We cann pass the arena along to other functions:

```
fn insert(arena: Arena, node: &Node, value: i32) {
    let new_node = Node:arena {value: value, next: null};
    node.next = new_node;
}
```

The `new_node` is now allocated in the `arena` arena.
