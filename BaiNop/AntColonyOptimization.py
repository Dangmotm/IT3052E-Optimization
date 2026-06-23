import time
from collections import defaultdict, deque
import random
random.seed(42)

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


class solution():
    def __init__(self, task_order, team_assignment):
        self.task_order = task_order
        self.team_assignment = team_assignment


def decode_solution(cur_state, duration, num_task, team_avaiable, rev_graph):
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
    schedule = decode_solution(cur_state, duration, num_task, team_avaiable, rev_graph)
    finish_task, completion, totalCost = 0, 0, 0

    for task, team, start in schedule:
        finish_task += 1
        finish = start + duration[task]
        if finish > completion:
            completion = finish
        totalCost += cost[task][team]

    return (num_task - finish_task, completion, totalCost)


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

    return solution(task_order, team_assignment)


def init_pheromone(schedulable_order, available_team):
    tau = {}
    for task in schedulable_order:
        tau[task] = {team: tau0 for team in available_team[task]}
    return tau


def ant_construct(schedulable_order, rev_graph, available_team, duration, team_avaiable,
                  tau, alpha, beta):

    task_End = [0] * num_task
    teamAvaiable = team_avaiable[:]
    task_order = []
    team_assignment = []

    for currentTask in schedulable_order:
        pred_finish = 0
        for p in rev_graph[currentTask]:
            if pred_finish < task_End[p]:
                pred_finish = task_End[p]

        # Compute weight for each available team
        weights = []
        teams = available_team[currentTask]
        for team in teams:
            earliest = max(teamAvaiable[team], pred_finish)
            finish = earliest + duration[currentTask]
            eta = 1.0 / (finish + 1)
            w = (tau[currentTask][team] ** alpha) * (eta ** beta)
            weights.append(w)

        # Roulette-wheel selection
        total = sum(weights)
        if total == 0:
            chosen_team = random.choice(teams)
        else:
            r = random.random() * total
            cumulative = 0.0
            chosen_team = teams[-1]
            for team, w in zip(teams, weights):
                cumulative += w
                if cumulative >= r:
                    chosen_team = team
                    break

        earliest = max(teamAvaiable[chosen_team], pred_finish)
        task_End[currentTask] = earliest + duration[currentTask]
        teamAvaiable[chosen_team] = task_End[currentTask]
        task_order.append(currentTask)
        team_assignment.append(chosen_team)

    return solution(task_order, team_assignment)


def evaporate(tau, rho):
    for task in tau:
        for team in tau[task]:
            tau[task][team] *= (1.0 - rho)
            tau[task][team] = max(tau_min, tau[task][team])


def deposit(tau, sol, fitness):
    _, completion, _ = fitness
    delta = 1.0 / (completion + 1)
    for task, team in zip(sol.task_order, sol.team_assignment):
        tau[task][team] += delta
        tau[task][team] = min(tau_max, tau[task][team])


start_time = time.time()
max_time = 295.0

num_ants = 10          # số kiến mỗi vòng
alpha = 1.0            # trọng số pheromone
beta = 2.0             # trọng số heuristic
rho = 0.1              # tỉ lệ bay hơi
tau0 = 1.0             # pheromone khởi tạo
tau_min = 1e-4         # giới hạn dưới pheromone (MMAS)
tau_max = 10.0         # giới hạn trên pheromone (MMAS)

# Khởi tạo pheromone
tau = init_pheromone(schedulable_order, available_team)

# Seed bằng greedy solution
best = greedy_construct(schedulable_order, rev_graph, s, task_duration, cost)
f_best = calc_fitness(best, num_task, cost, task_duration, s, rev_graph)

# Deposit pheromone từ greedy solution ban đầu
deposit(tau, best, f_best)

while True:
    elapsed = time.time() - start_time
    if elapsed >= max_time:
        break

    # Mỗi kiến xây một solution
    iteration_best = None
    f_iteration_best = None

    for _ in range(num_ants):
        ant_sol = ant_construct(schedulable_order, rev_graph, available_team, task_duration, s,
                                tau, alpha, beta)
        f_ant = calc_fitness(ant_sol, num_task, cost, task_duration, s, rev_graph)

        # Cập nhật iteration best
        if f_iteration_best is None or f_ant < f_iteration_best:
            iteration_best = ant_sol
            f_iteration_best = f_ant

        # Cập nhật global best
        if f_ant < f_best:
            best = ant_sol
            f_best = f_ant

    # Bay hơi pheromone
    evaporate(tau, rho)

    # Deposit: dùng global best (exploitation) kết hợp iteration best (exploration)
    deposit(tau, best, f_best)
    if iteration_best is not None:
        deposit(tau, iteration_best, f_iteration_best)

schedule = decode_solution(best, task_duration, num_task, s, rev_graph)
schedule.sort()
print(R)
for task, team, start in schedule:
    print(task + 1, team + 1, start)
