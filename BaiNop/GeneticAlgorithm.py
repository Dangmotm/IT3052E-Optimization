import time
from collections import defaultdict, deque
import random
random.seed(42)

#input
num_task, Q_constraint = map(int, input().split())

precedence = []
for _ in range(Q_constraint):
    u, v = map(int, input().split())
    precedence.append((u - 1, v - 1))

precedence_graph = {u: [] for u in range(num_task)}
rev_graph = {v: [] for v in range(num_task)}
for (u, v) in precedence:
    precedence_graph[u].append(v)
    rev_graph[v].append(u)

task_duration = list(map(int, input().split()))

num_team = int(input())
s = list(map(int, input().split()))

K = int(input())
cost = defaultdict(dict)
can_do = [0 for _ in range(num_task)]
for _ in range(K):
    i, j, w = map(int, input().split())
    i -= 1
    j -= 1

    can_do[i] = 1
    cost[i][j] = w

available_team = [list(cost[i].keys()) for i in range(num_task)]


def compute_schedulable_order(num_task, precedence_graph, can_do):
    in_deg = [0] * num_task
    for u in range(num_task):
        for v in precedence_graph[u]:
            in_deg[v] += 1

    queue = deque()
    for i in range(num_task):
        if in_deg[i] == 0: queue.append(i)

    in_deg2 = in_deg[:]
    full_order = []
    while queue:
        u = queue.popleft()
        full_order.append(u)
        for v in precedence_graph[u]:
            in_deg2[v] -= 1
            if in_deg2[v] == 0:
                queue.append(v)

    return [u for u in full_order if can_do[u]]

schedulable_order = compute_schedulable_order(num_task, precedence_graph, can_do)
R = len(schedulable_order)

class chromosome():
    def __init__(self, task_order, team_assignment):
        self.task_order = task_order
        self.team_assignment = team_assignment


def greedy_construct(schedulable_order, rev_graph, team_avaiable, duration, cost):
    task_End = [0] * num_task
    teamAvaiable = team_avaiable[:]
    task_order = []
    team_assignment = []
    for currentTask in schedulable_order:
        pred_finish = 0
        for p in rev_graph[currentTask]:
            if task_End[p] > pred_finish:
                pred_finish = task_End[p]

        best_choice = None
        best_time = float('inf')
        best_cost = float('inf')

        for team, c in cost[currentTask].items():
            earliest = max(teamAvaiable[team], pred_finish)
            if earliest < best_time or (earliest == best_time and c < best_cost):
                best_time = earliest
                best_cost = c
                best_choice = team
        
        task_order.append(currentTask)
        team_assignment.append(best_choice)
        task_End[currentTask] += best_time + duration[currentTask]
        teamAvaiable[best_choice] = task_End[currentTask]
    
    return chromosome(task_order, team_assignment)

def decode_chromosome(cur_state, duration, num_task, team_avaiable, rev_graph):
    task_End = [0] * num_task
    teamAvaiable = team_avaiable[:]
    schedule = []

    task_order, team_assignment = cur_state.task_order, cur_state.team_assignment
    
    for currentTask, team in zip(task_order, team_assignment):
        pred_finish = 0
        for p in rev_graph[currentTask]:
            if task_End[p] > pred_finish:
                pred_finish = task_End[p]
        
        earliest = max(teamAvaiable[team], pred_finish)
        teamAvaiable[team] = earliest + duration[currentTask]
        task_End[currentTask] = earliest + duration[currentTask]
        schedule.append((currentTask, team, earliest))
    
    return schedule

def calc_fitness(cur_state, num_task, cost, duration, team_avaiable, rev_graph):

    schedule = decode_chromosome(cur_state, duration, num_task, team_avaiable, rev_graph)
    finish_task, completion, totalCost = 0, 0, 0

    for task, team, start in schedule:
        finish_task += 1
        finish = start + duration[task]
        if finish > completion:
            completion = finish
        totalCost += cost[task][team] 

    return (num_task - finish_task, completion, totalCost)

def is_precedence_feasible(task_order, precedence):
    pos = {task: idx for idx, task in enumerate(task_order)}
    for (i, j) in precedence:
        if i in pos and j in pos:
            if pos[i] >= pos[j]:
                return False
    return True

def topological_repair(task_order, precedence_graph):
    """Repair a task_order to satisfy precedence constraints via topological sort,
    keeping only schedulable tasks."""
    task_set = set(task_order)
    in_deg = defaultdict(int)
    for u in task_set:
        if u not in in_deg:
            in_deg[u] = 0
        for v in precedence_graph[u]:
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
        for v in precedence_graph[u]:
            if v in task_set:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    queue.append(v)

    return result


def construct_random(schedulable_order, precedence_graph, available_team):
    """Construct a random individual with shuffled topological order."""
    task_set = set(schedulable_order)
    in_deg = defaultdict(int)
    for u in task_set:
        if u not in in_deg:
            in_deg[u] = 0
        for v in precedence_graph[u]:
            if v in task_set:
                in_deg[v] += 1

    ready = []
    for t in schedulable_order:
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
        for v in precedence_graph[pick]:
            if v in task_set:
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    ready.append(v)

    team_assignment = [random.choice(available_team[i]) for i in task_order]
    return chromosome(task_order, team_assignment)


def initialize_population(population_size, schedulable_order, rev_graph, precedence_graph,
                          available_team, team_avaiable, cost, duration):
    population = []
    # First individual: greedy
    ind = greedy_construct(schedulable_order, rev_graph, team_avaiable, duration, cost)
    population.append(ind)
    # Remaining: random feasible individuals
    for _ in range(population_size - 1):
        ind = construct_random(schedulable_order, precedence_graph, available_team)
        population.append(ind)
    return population


def rank_selection(population, num_task, cost, duration, team_avaiable, rev_graph):
    population = sorted(population, key=lambda x: calc_fitness(x, num_task, cost, duration, team_avaiable, rev_graph))
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


def POX(parent1, parent2, precedence, precedence_graph):
    """Precedence-preserving Order Crossover."""
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
    if not is_precedence_feasible(child, precedence):
        child = topological_repair(child, precedence_graph)
    return child

def TAX(task_order1, team1, task_order2, team2, available_team, child_task_order):
    """Team Assignment Crossover.
    For each task in the child, pick the team assigned by parent1 or parent2
    (looked up by task identity, not position).
    """
    map1 = {task: team for task, team in zip(task_order1, team1)}
    map2 = {task: team for task, team in zip(task_order2, team2)}
    child_team = []
    for currentTask in child_task_order:
        possible = []
        if currentTask in map1 and map1[currentTask] in available_team[currentTask]:
            possible.append(map1[currentTask])
        if currentTask in map2 and map2[currentTask] in available_team[currentTask]:
            possible.append(map2[currentTask])
        if possible:
            child_team.append(random.choice(possible))
        else:
            child_team.append(random.choice(available_team[currentTask]))
    return child_team

def offspring_generate(parent1, parent2, precedence, precedence_graph, available_team):
    task_order1, team1 = parent1.task_order, parent1.team_assignment
    task_order2, team2 = parent2.task_order, parent2.team_assignment
    
    child_task1 = POX(task_order1, task_order2, precedence, precedence_graph)
    child_task2 = POX(task_order2, task_order1, precedence, precedence_graph)

    child_team1 = TAX(task_order1, team1, task_order2, team2, available_team, child_task1)
    child_team2 = TAX(task_order2, team2, task_order1, team1, available_team, child_task2)

    child1 = chromosome(child_task1, child_team1)
    child2 = chromosome(child_task2, child_team2)
    return child1, child2

def task_order_mutation(task_order, team_assignment, precedence, attempts):
    if len(task_order) < 2:
        return task_order[:]

    for _ in range(attempts):
        new_order = task_order[:]
        i, j = random.sample(range(len(new_order)), 2)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        if is_precedence_feasible(new_order, precedence):
            team_assignment[i], team_assignment[j] = team_assignment[j], team_assignment[i]
            return new_order
    return task_order

def team_assignment_mutation(task_order, team_assignment, available_team, mutation_rate):
    new_assignment = team_assignment[:]
    for idx, task in enumerate(task_order):
        if random.random() < mutation_rate:
            viable = available_team[task]
            if len(viable) > 1:
                old_team = new_assignment[idx]
                new_team = old_team
                while new_team == old_team:
                    new_team = random.choice(viable)
                new_assignment[idx] = new_team
    return new_assignment

def mutate(ind, precedence, available_team, attempts = 5, mutation_rate = 0.05):
    task_order, team_assignment = ind.task_order[:], ind.team_assignment[:]
    new_task_order = task_order_mutation(task_order, team_assignment, precedence, attempts)
    new_team_assignment = team_assignment_mutation(new_task_order, team_assignment, available_team, mutation_rate)
    return chromosome(new_task_order, new_team_assignment)

def evaluate_and_replace(population, child1, child2, num_task, cost, duration, team_avaiable, rev_graph):
    population_size = len(population)
    population.extend([child1, child2])
    population.sort(key=lambda x: calc_fitness(x, num_task, cost, duration, team_avaiable, rev_graph))
    return population[:population_size]


start = time.time()
max_time = 295.0
population_size = 10

population = initialize_population(population_size, schedulable_order, rev_graph, precedence_graph,
                                   available_team, s, cost, task_duration)

while True:
    elapsed = time.time() - start
    if elapsed >= max_time:
        break

    parent1, parent2 = rank_selection(population, num_task, cost, task_duration, s, rev_graph)
    child1, child2 = offspring_generate(parent1, parent2, precedence, precedence_graph, available_team)
    child1 = mutate(child1, precedence, available_team)
    child2 = mutate(child2, precedence, available_team)
    population = evaluate_and_replace(population, child1, child2, num_task, cost, task_duration, s, rev_graph)

best = population[0]
schedule = decode_chromosome(best, task_duration, num_task, s, rev_graph)
schedule.sort()
print(R)
for task, team, start in schedule:
    print(task + 1, team + 1, start)
