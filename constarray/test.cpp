const double G = 9.8;
const double dt = 0.01;
const int N = 10000;

void func(double v[N]) {
  for (int i = 0; i < N; i++) {
    v[i] += G * dt;
  }
}
