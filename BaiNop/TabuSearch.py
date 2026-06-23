import time
import math
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

class state():
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
    
    return state(task_order, team_assignment)

def decode_state(cur_state, duration, num_task, team_avaiable, rev_graph):
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

    schedule = decode_state(cur_state, duration, num_task, team_avaiable,rev_graph)
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

def task_order_mutation(task_order, team_assignment, precedence, attempts):
    if len(task_order) < 2:                                    
        return task_order[:], team_assignment[:], None
    
    for _ in range(attempts):
        new_order = task_order[:]
        i, j = random.sample(range(len(new_order)), 2)
        new_order[i], new_order[j] = new_order[j], new_order[i]
        if is_precedence_feasible(new_order, precedence):
            new_team = team_assignment[:]
            new_team[i], new_team[j] = new_team[j], new_team[i]
            swap_key = tuple(sorted((task_order[i], task_order[j])))
            return new_order, new_team, swap_key
    return task_order[:], team_assignment[:], None

def team_assignment_mutation(task_order, team_assignment, available_team, mutation_rate):
    new_assignment = team_assignment[:]
    changes = []
    for idx, task in enumerate(task_order):
        if random.random() < mutation_rate:
            viable = available_team[task]
            if len(viable) > 1:
                new_team = random.choice(viable)
                if new_team == new_assignment[idx]:
                    new_team = random.choice(viable)
                if new_team != new_assignment[idx]:
                    changes.append((task, new_assignment[idx], new_team))
                    new_assignment[idx] = new_team
    return new_assignment, changes


def get_neighbor(cur, precedence, available_team, attempts = 5, mutation_rate = 0.1):
    new_task_order, team_after_swap, swap_key = task_order_mutation(cur.task_order, cur.team_assignment, precedence, attempts)
    new_team_assignment, team_changes = team_assignment_mutation(new_task_order, team_after_swap, available_team, mutation_rate)
    move = (swap_key, tuple(team_changes))
    return state(new_task_order, new_team_assignment), move


def is_tabu(move, tabu_swap, tabu_team, gen):
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


def register_tabu(move, tabu_swap, tabu_team, gen, tenure):
    swap_key, team_changes = move
    if swap_key is not None:
        tabu_swap[swap_key] = gen + tenure
    for (task, old_team, new_team) in team_changes:
        tabu_team[(task, old_team)] = gen + tenure



start_time = time.time()          
max_time = 295.0
num_neighbors = 10
attempts = 5
mutation_rate = 0.1
tabu_tenure = 10

tabu_swap = {}
tabu_team = {}

curr = greedy_construct(schedulable_order, rev_graph, s, task_duration, cost)
f_curr = calc_fitness(curr, num_task, cost, task_duration, s, rev_graph)
best = curr
f_best = f_curr

gen = 0
while True:
    if time.time() - start_time >= max_time:
        break
    gen += 1

    best_candidate, best_candidate_fit, best_candidate_move = None, None, None

    for _ in range(num_neighbors):
        neighbor, move = get_neighbor(curr, precedence, available_team, attempts, mutation_rate)
        fit = calc_fitness(neighbor, num_task, cost, task_duration, s, rev_graph)
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

schedule = decode_state(best, task_duration, num_task, s, rev_graph)
schedule.sort()
print(R)
for task, team, start in schedule:
    print(task + 1, team + 1, start)


