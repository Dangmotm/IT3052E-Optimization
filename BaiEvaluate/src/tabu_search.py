import time
import random

try:
    from .base import State, read_input, decode_state, load_algorithm_config
except ImportError:
    from base import State, read_input, decode_state, load_algorithm_config


class TS:
    def __init__(self, problem, config):
        self.problem = problem
        self.max_time = float(config.max_time)
        self.num_neighbors = int(config.num_neighbors)
        self.attempts = int(config.attempts)
        self.mutation_rate = float(config.mutation_rate)
        self.tabu_tenure = int(config.tabu_tenure)

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
            return task_order[:], team_assignment[:], None

        for _ in range(attempts):
            new_order = task_order[:]
            i, j = random.sample(range(len(new_order)), 2)
            new_order[i], new_order[j] = new_order[j], new_order[i]
            if self.is_precedence_feasible(new_order):
                new_team = team_assignment[:]
                new_team[i], new_team[j] = new_team[j], new_team[i]
                swap_key = tuple(sorted((task_order[i], task_order[j])))
                return new_order, new_team, swap_key
        return task_order[:], team_assignment[:], None

    def team_assignment_mutation(self, task_order, team_assignment, mutation_rate):
        new_assignment = team_assignment[:]
        changes = []
        for idx, task in enumerate(task_order):
            if random.random() < mutation_rate:
                viable = self.problem.available_team[task]
                if len(viable) > 1:
                    new_team = random.choice(viable)
                    if new_team == new_assignment[idx]:
                        new_team = random.choice(viable)
                    if new_team != new_assignment[idx]:
                        changes.append((task, new_assignment[idx], new_team))
                        new_assignment[idx] = new_team
        return new_assignment, changes

    def get_neighbor(self, cur, attempts = 5, mutation_rate = 0.1):
        new_task_order, team_after_swap, swap_key = self.task_order_mutation(cur.task_order, cur.team_assignment, attempts)
        new_team_assignment, team_changes = self.team_assignment_mutation(new_task_order, team_after_swap, mutation_rate)
        move = (swap_key, tuple(team_changes))
        return State(new_task_order, new_team_assignment), move

    def is_tabu(self, move, tabu_swap, tabu_team, gen):
        swap_key, team_changes = move
        if swap_key is not None:
            expire = tabu_swap.get(swap_key)
            if expire is not None and expire > gen:
                return True
        for (task, old_team, new_team) in team_changes:
            expire = tabu_team.get((task, new_team))
            if expire is not None and expire > gen:
                return True
        return False

    def register_tabu(self, move, tabu_swap, tabu_team, gen, tenure):
        swap_key, team_changes = move
        if swap_key is not None:
            tabu_swap[swap_key] = gen + tenure
        for (task, old_team, new_team) in team_changes:
            tabu_team[(task, old_team)] = gen + tenure

    def solve(self):
        start_time = time.time()
        max_time = self.max_time
        num_neighbors = self.num_neighbors
        attempts = self.attempts
        mutation_rate = self.mutation_rate
        tabu_tenure = self.tabu_tenure
        get_neighbor = self.get_neighbor
        calc_fitness = self.calc_fitness
        is_tabu = self.is_tabu
        register_tabu = self.register_tabu
        current_time = time.time

        tabu_swap = {}
        tabu_team = {}

        curr = self.greedy_construct()
        f_curr = calc_fitness(curr)
        best = curr
        f_best = f_curr

        gen = 0
        while True:
            if current_time() - start_time >= max_time:
                break
            gen += 1

            best_candidate, best_candidate_fit, best_candidate_move = None, None, None

            for _ in range(num_neighbors):
                neighbor, move = get_neighbor(curr, attempts, mutation_rate)
                fit = calc_fitness(neighbor)
                admissible = (not is_tabu(move, tabu_swap, tabu_team, gen)) or (fit < f_best)
                if admissible and (best_candidate_fit is None or fit < best_candidate_fit):
                    best_candidate, best_candidate_fit, best_candidate_move = neighbor, fit, move

            if best_candidate is None:
                continue

            curr, f_curr = best_candidate, best_candidate_fit
            if f_curr < f_best:
                best, f_best = curr, f_curr

            register_tabu(best_candidate_move, tabu_swap, tabu_team, gen, tabu_tenure)

            if gen % 200 == 0:
                tabu_swap = {k: v for k, v in tabu_swap.items() if v > gen}
                tabu_team = {k: v for k, v in tabu_team.items() if v > gen}

        return best


def main():
    problem = read_input()
    config, seed = load_algorithm_config("TS")
    random.seed(seed)
    best = TS(problem, config).solve()
    schedule = decode_state(best, problem)
    schedule.sort()
    print(len(problem.schedulable_order))
    for task, team, start in schedule:
        print(task + 1, team + 1, start)


if __name__ == "__main__":
    main()
