import time
import math
import random

try:
    from .base import State, read_input, decode_state, load_algorithm_config
except ImportError:
    from base import State, read_input, decode_state, load_algorithm_config


class SA:
    def __init__(self, problem, config):
        self.problem = problem
        self.max_time = float(config.max_time)
        self.T0 = float(config.T0)
        self.t_min = float(config.t_min)
        self.attempts = int(config.attempts)
        self.mutation_rate = float(config.mutation_rate)

    def greedy_construct(self):
        problem = self.problem
        task_End = [0] * problem.num_task
        teamAvaiable = problem.s[:]
        task_order = []
        team_assignment = []
        for currentTask in problem.schedulable_order:
            pred_finish = 0
            for p in problem.rev_graph[currentTask]:
                if task_End[p] > pred_finish:
                    pred_finish = task_End[p]

            best_choice = None
            best_time = float('inf')
            best_cost = float('inf')

            for team, c in problem.cost[currentTask].items():
                earliest = max(teamAvaiable[team], pred_finish)
                if earliest < best_time or (earliest == best_time and c < best_cost):
                    best_time = earliest
                    best_cost = c
                    best_choice = team

            task_order.append(currentTask)
            team_assignment.append(best_choice)
            task_End[currentTask] += best_time + problem.duration[currentTask]
            teamAvaiable[best_choice] = task_End[currentTask]

        return State(task_order, team_assignment)

    def calc_fitness(self, cur_state):
        problem = self.problem
        task_End = [0] * problem.num_task
        teamAvaiable = problem.s[:]
        finish_task, completion, totalCost = 0, 0, 0

        task_order, team_assignment = cur_state.task_order, cur_state.team_assignment

        for currentTask, team in zip(task_order, team_assignment):
            pred_finish = 0
            for p in problem.rev_graph[currentTask]:
                if task_End[p] > pred_finish:
                    pred_finish = task_End[p]

            earliest = max(teamAvaiable[team], pred_finish)
            finish = earliest + problem.duration[currentTask]
            teamAvaiable[team] = finish
            task_End[currentTask] = finish
            finish_task += 1
            if finish > completion:
                completion = finish
            totalCost += problem.cost[currentTask][team]

        return (problem.num_task - finish_task, completion, totalCost)

    def is_precedence_feasible(self, task_order):
        pos = {task: idx for idx, task in enumerate(task_order)}
        for (i, j) in self.problem.precedence:
            if i in pos and j in pos:
                if pos[i] >= pos[j]:
                    return False
        return True

    def task_order_mutation(self, task_order, team_assignment, attempts):
        if len(task_order) < 2:
            return task_order[:]

        for _ in range(attempts):
            new_order = task_order[:]
            i, j = random.sample(range(len(new_order)), 2)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if self.is_precedence_feasible(new_order):
                team_assignment[i], team_assignment[j] = team_assignment[j], team_assignment[i]
                return new_order
        return task_order

    def team_assignment_mutation(self, task_order, team_assignment, mutation_rate):
        new_assignment = team_assignment[:]
        for idx, task in enumerate(task_order):
            if random.random() < mutation_rate:
                viable = self.problem.available_team[task]
                if len(viable) > 1:
                    old_team = new_assignment[idx]
                    new_team = old_team
                    while new_team == old_team:
                        new_team = random.choice(viable)
                    new_assignment[idx] = new_team
        return new_assignment

    def get_neighbor(self, cur, attempts = 5, mutation_rate = 0.1):
        task_order, team_assignment = cur.task_order[:], cur.team_assignment[:]
        new_task_order = self.task_order_mutation(task_order, team_assignment, attempts)
        new_team_assignment = self.team_assignment_mutation(new_task_order, team_assignment, mutation_rate)
        return State(new_task_order, new_team_assignment)

    def acceptance(self, f_curr, f_neigh, temperature):
        if f_neigh <= f_curr:
            return True

        for a, b in zip(f_curr, f_neigh):
            if a != b:
                delta = (b - a) / max(1.0, abs(a))
                break

        prob = math.exp(-delta / temperature)
        return random.random() <= prob

    def solve(self):
        start = time.time()
        max_time = self.max_time
        T0 = self.T0
        t_min = self.t_min
        attempts = self.attempts
        mutation_rate = self.mutation_rate
        get_neighbor = self.get_neighbor
        calc_fitness = self.calc_fitness
        acceptance = self.acceptance
        current_time = time.time

        curr = self.greedy_construct()
        best = curr
        f_curr = calc_fitness(curr)
        f_best = f_curr

        while True:
            elapsed = current_time() - start
            if elapsed >= max_time:
                break

            temperature = max(t_min, T0 * (1.0 - elapsed / max_time))

            neighbor = get_neighbor(curr, attempts = attempts, mutation_rate = mutation_rate)
            f_neigh = calc_fitness(neighbor)

            if acceptance(f_curr, f_neigh, temperature):
                curr, f_curr = neighbor, f_neigh
                if f_neigh < f_best:
                    best, f_best = neighbor, f_neigh

        return best


def main():
    problem = read_input()
    config, seed = load_algorithm_config("SA")
    random.seed(seed)
    best = SA(problem, config).solve()
    schedule = decode_state(best, problem)
    schedule.sort()
    print(len(problem.schedulable_order))
    for task, team, start in schedule:
        print(task + 1, team + 1, start)


if __name__ == "__main__":
    main()
