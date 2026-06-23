import time
from collections import defaultdict, deque
import random

try:
    from .base import State, read_input, decode_state, load_algorithm_config
except ImportError:
    from base import State, read_input, decode_state, load_algorithm_config


class GA:
    def __init__(self, problem, config):
        self.problem = problem
        self.max_time = float(config.max_time)
        self.population_size = int(config.population_size)
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

    def topological_repair(self, task_order):
        task_set = set(task_order)
        in_deg = defaultdict(int)
        for u in task_set:
            if u not in in_deg:
                in_deg[u] = 0
            for v in self.problem.precedence_graph[u]:
                if v in task_set:
                    in_deg[v] += 1

        queue = deque()
        for t in task_order:
            if in_deg[t] == 0:
                queue.append(t)

        result = []
        visited = set()
        while queue:
            u = queue.popleft()
            if u in visited:
                continue
            visited.add(u)
            result.append(u)
            for v in self.problem.precedence_graph[u]:
                if v in task_set:
                    in_deg[v] -= 1
                    if in_deg[v] == 0:
                        queue.append(v)

        return result

    def construct_random(self):
        task_set = set(self.problem.schedulable_order)
        in_deg = defaultdict(int)
        for u in task_set:
            if u not in in_deg:
                in_deg[u] = 0
            for v in self.problem.precedence_graph[u]:
                if v in task_set:
                    in_deg[v] += 1

        ready = []
        for t in self.problem.schedulable_order:
            if in_deg[t] == 0:
                ready.append(t)

        task_order = []
        visited = set()
        while ready:
            pick = random.choice(ready)
            ready.remove(pick)
            if pick in visited:
                continue
            visited.add(pick)
            task_order.append(pick)
            for v in self.problem.precedence_graph[pick]:
                if v in task_set:
                    in_deg[v] -= 1
                    if in_deg[v] == 0:
                        ready.append(v)

        team_assignment = [random.choice(self.problem.available_team[i]) for i in task_order]
        return State(task_order, team_assignment)

    def initialize_population(self):
        population = []
        # First individual: greedy
        ind = self.greedy_construct()
        population.append(ind)
        # Remaining: random feasible individuals
        for _ in range(self.population_size - 1):
            ind = self.construct_random()
            population.append(ind)
        return population

    def rank_selection(self, population):
        population = sorted(population, key=lambda x: self.calc_fitness(x))
        k = len(population)
        probs = [0] * k
        sp = 1.5
        for i in range(k):
            probs[i] = 1 / k * (sp - (2 * sp - 2) * i / (k - 1))

        # Roulette-wheel selection
        for i in range(1, k):
            probs[i] += probs[i - 1]

        parents = []
        for _ in range(2):
            r = random.random()
            chosen = population[-1]
            for i in range(k):
                if probs[i] >= r:
                    chosen = population[i]
                    break
            parents.append(chosen)
        return parents[0], parents[1]

    def POX(self, parent1, parent2):
        child = [-1] * len(parent1)
        added = set()
        for i in range(len(parent1)):
            r = random.random()
            if r >= 0.5:
                child[i] = parent1[i]
                added.add(parent1[i])
        j = 0
        for i in range(len(child)):
            if child[i] == -1:
                while parent2[j] in added:
                    j += 1
                child[i] = parent2[j]
                added.add(parent2[j])
                j += 1
        if not self.is_precedence_feasible(child):
            child = self.topological_repair(child)
        return child

    def TAX(self, task_order1, team1, task_order2, team2, child_task_order):
        map1 = {task: team for task, team in zip(task_order1, team1)}
        map2 = {task: team for task, team in zip(task_order2, team2)}
        child_team = []
        for currentTask in child_task_order:
            possible = []
            if currentTask in map1 and map1[currentTask] in self.problem.available_team[currentTask]:
                possible.append(map1[currentTask])
            if currentTask in map2 and map2[currentTask] in self.problem.available_team[currentTask]:
                possible.append(map2[currentTask])
            if possible:
                child_team.append(random.choice(possible))
            else:
                child_team.append(random.choice(self.problem.available_team[currentTask]))
        return child_team

    def offspring_generate(self, parent1, parent2):
        task_order1, team1 = parent1.task_order, parent1.team_assignment
        task_order2, team2 = parent2.task_order, parent2.team_assignment

        child_task1 = self.POX(task_order1, task_order2)
        child_task2 = self.POX(task_order2, task_order1)

        child_team1 = self.TAX(task_order1, team1, task_order2, team2, child_task1)
        child_team2 = self.TAX(task_order2, team2, task_order1, team1, child_task2)

        child1 = State(child_task1, child_team1)
        child2 = State(child_task2, child_team2)
        return child1, child2

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

    def mutate(self, ind, attempts = 5, mutation_rate = 0.05):
        task_order, team_assignment = ind.task_order[:], ind.team_assignment[:]
        new_task_order = self.task_order_mutation(task_order, team_assignment, attempts)
        new_team_assignment = self.team_assignment_mutation(new_task_order, team_assignment, mutation_rate)
        return State(new_task_order, new_team_assignment)

    def evaluate_and_replace(self, population, child1, child2):
        population_size = len(population)
        population.extend([child1, child2])
        population.sort(key=lambda x: self.calc_fitness(x))
        return population[:population_size]

    def solve(self):
        start = time.time()
        max_time = self.max_time
        attempts = self.attempts
        mutation_rate = self.mutation_rate
        rank_selection = self.rank_selection
        offspring_generate = self.offspring_generate
        mutate = self.mutate
        evaluate_and_replace = self.evaluate_and_replace
        current_time = time.time

        population = self.initialize_population()

        while True:
            elapsed = current_time() - start
            if elapsed >= max_time:
                break

            parent1, parent2 = rank_selection(population)
            child1, child2 = offspring_generate(parent1, parent2)
            child1 = mutate(child1, attempts, mutation_rate)
            child2 = mutate(child2, attempts, mutation_rate)
            population = evaluate_and_replace(population, child1, child2)

        return population[0]


def main():
    problem = read_input()
    config, seed = load_algorithm_config("GA")
    random.seed(seed)
    best = GA(problem, config).solve()
    schedule = decode_state(best, problem)
    schedule.sort()
    print(len(problem.schedulable_order))
    for task, team, start in schedule:
        print(task + 1, team + 1, start)


if __name__ == "__main__":
    main()
