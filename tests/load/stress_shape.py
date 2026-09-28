"""
Стресс: ступенчатый рост пользователей до точки деградации (только 127.0.0.1).

    locust -f tests/load/locustfile.py,tests/load/stress_shape.py --headless --host http://127.0.0.1:8766 \
           --csv docs/evidence/locust/stress
Ступени по 60 с: 10 → 25 → 50 → 100 → 150 → 200 VU. KioskUser (1) и StreamUser (3) — фиксированы,
растут гости/оператор/WS — именно они масштабируются на фестивале.
"""
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    steps = [10, 25, 50, 100, 150, 200]
    step_seconds = 60

    def tick(self):
        run_time = self.get_run_time()
        idx = int(run_time // self.step_seconds)
        if idx >= len(self.steps):
            return None
        return self.steps[idx], max(5, self.steps[idx] // 5)
