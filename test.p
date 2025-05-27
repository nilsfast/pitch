fn do_stuff(a: Box(int), b: int) -> Box(int) {
    return Box(*a + b);
}

fn test_alloc(value: int) -> Box(int) {
    let not_returned = Box(100);
    let dead = Box(100);
    not_returned = do_stuff(not_returned, value);
    return Box(100);
}

fn main() -> int {
    let a = 10;
    let c = test_alloc(a);
    let b = do_stuff(c, 1);
    return 0;
}
