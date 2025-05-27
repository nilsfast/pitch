#include <stdio.h>
#include <stdlib.h>

int *Box(int a) {
	int *p = malloc(sizeof(*p));
	if (p != NULL) {
		*p = a;
	}
	return p;
}

//
int *test_alloc(int value) {
	int *not_returned = Box(100);
	int *not_returned2 = Box(100);
	free(not_returned);
	not_returned = not_returned2;
	free(not_returned2);
	return Box(value);
}
int *do_stuff(int *a) { return a; }
int main() {
	int a = 10;
	int *c = test_alloc(a);
	int *test = c;
	int *b = do_stuff(c);
	return 0;
	free(test);
	free(b);
}