int *test(void) {
	int a = 1;
	return &a;
}
int main(void) {
	int *b = test();
	return 0;
}