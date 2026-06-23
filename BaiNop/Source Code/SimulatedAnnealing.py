import time
import math
from collections import defaultdict, deque
import random
random.seed(42)
import math

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

def get_neighbor(cur, precedence, available_team, attempts = 5, mutation_rate = 0.1):
    task_order, team_assignment = cur.task_order[:], cur.team_assignment[:]
    new_task_order = task_order_mutation(task_order, team_assignment, precedence, attempts)
    new_team_assignment = team_assignment_mutation(new_task_order, team_assignment, available_team, mutation_rate)
    return state(new_task_order, new_team_assignment)

def acceptance(f_curr, f_neigh, temperature):
    if f_neigh <= f_curr:
        return True

    for a, b in zip(f_curr, f_neigh):
        if a != b:
            delta = (b - a) / max(1.0, abs(a))
            break

    prob = math.exp(-delta / temperature)
    return random.random() <= prob

start = time.time()
max_time = 295.0
T0 = 50.0          
t_min = 1e-3
 
curr = greedy_construct(schedulable_order, rev_graph, s, task_duration, cost)
best = curr
f_curr = calc_fitness(curr, num_task, cost, task_duration, s, rev_graph)
f_best = f_curr
 
while True:
    elapsed = time.time() - start
    if elapsed >= max_time:
        break

    temperature = max(t_min, T0 * (1.0 - elapsed / max_time))   
 
    neighbor = get_neighbor(curr, precedence, available_team, attempts = 5, mutation_rate = 0.1)
    f_neigh = calc_fitness(neighbor, num_task, cost, task_duration, s, rev_graph)
 
    if acceptance(f_curr, f_neigh, temperature):
        curr, f_curr = neighbor, f_neigh           
        if f_neigh < f_best:
            best, f_best = neighbor, f_neigh

schedule = decode_state(best, task_duration, num_task, s, rev_graph)
schedule.sort()
print(R)
for task, team, start in schedule:
    print(task + 1, team + 1, start)