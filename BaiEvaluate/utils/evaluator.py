import random
import time
from collections import defaultdict

from src.ant_colony import ACO
from src.genetic_algorithm import GA
from src.simulated_annealing import SA
from src.tabu_search import TS
from src.base import Problem, calc_fitness, compute_schedulable_order


class Evaluator:
    def read_input(self, path):
        with open(path, "r") as f:
            num_task, Q_constraint = map(int, f.readline().split())

            precedence = []
            precedence_graph = {u: [] for u in range(num_task)}
            rev_graph = {v: [] for v in range(num_task)}

            for _ in range(Q_constraint):
                u, v = map(int, f.readline().split())
                u -= 1
                v -= 1
                precedence.append((u, v))
                precedence_graph[u].append(v)
                rev_graph[v].append(u)

            task_duration = list(map(int, f.readline().split()))
            num_team = int(f.readline())
            s = list(map(int, f.readline().split()))

            K = int(f.readline())
            cost = defaultdict(dict)
            can_do = [0] * num_task

            for _ in range(K):
                i, j, w = map(int, f.readline().split())
                i -= 1
                j -= 1

                can_do[i] = 1
                cost[i][j] = w

        problem = Problem()
        problem.num_task = num_task
        problem.precedence = precedence
        problem.precedence_graph = precedence_graph
        problem.rev_graph = rev_graph
        problem.duration = task_duration
        problem.num_team = num_team
        problem.s = s
        problem.cost = cost
        problem.available_team = [list(problem.cost[i].keys()) for i in range(problem.num_task)]
        problem.schedulable_order = compute_schedulable_order(problem, can_do)

        return problem

    def calc_score(self, problem, solution):
        missed_task, completion_time, total_cost = calc_fitness(solution, problem)
        finish_task = problem.num_task - missed_task
        return finish_task, completion_time, total_cost

    def evaluate(self, problem, cfg):
        methods = cfg["methods"]
        if cfg["only"] is not None:
            methods = [cfg["only"].upper()]

        print(f"[eval] evaluating methods on {cfg['current_test']}")
        results = defaultdict(dict)

        for method in methods:
            random.seed(cfg["seed"])
            solver = {
                "ACO": ACO,
                "GA": GA,
                "SA": SA,
                "TS": TS,
            }[method](problem, cfg["algorithm"][method])

            start = time.time()
            solution = solver.solve()
            end = time.time()

            results[method]["score"] = self.calc_score(problem, solution)
            results[method]["runtime"] = end - start
            print(f"    [{method.lower()}] score: {results[method]['score']}")
            print(f"    [{method.lower()}] runtime: {results[method]['runtime']}s")

        return cfg["current_test"], results
