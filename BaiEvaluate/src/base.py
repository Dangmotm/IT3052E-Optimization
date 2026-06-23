from collections import defaultdict, deque
from pathlib import Path

from omegaconf import OmegaConf


class Problem:
    def __init__(self):
        self.num_task = 0
        self.precedence = []
        self.precedence_graph = {}
        self.rev_graph = {}
        self.duration = []
        self.num_team = 0
        self.s = []
        self.cost = defaultdict(dict)
        self.available_team = []
        self.schedulable_order = []


class State:
    def __init__(self, task_order, team_assignment):
        self.task_order = task_order
        self.team_assignment = team_assignment


def load_algorithm_config(method):
    root = Path(__file__).resolve().parent.parent
    cfg = OmegaConf.load(root / "cfg" / "config.yaml")
    return cfg.algorithm[method], cfg.seed


def compute_schedulable_order(problem, can_do):
    in_deg = [0] * problem.num_task
    for u in range(problem.num_task):
        for v in problem.precedence_graph[u]:
            in_deg[v] += 1

    queue = deque()
    for i in range(problem.num_task):
        if in_deg[i] == 0: queue.append(i)

    in_deg2 = in_deg[:]
    full_order = []
    while queue:
        u = queue.popleft()
        full_order.append(u)
        for v in problem.precedence_graph[u]:
            in_deg2[v] -= 1
            if in_deg2[v] == 0:
                queue.append(v)

    return [u for u in full_order if can_do[u]]


def read_input():
    num_task, Q_constraint = map(int, input().split())

    precedence = []
    precedence_graph = {u: [] for u in range(num_task)}
    rev_graph = {v: [] for v in range(num_task)}

    for _ in range(Q_constraint):
        u, v = map(int, input().split())
        u -= 1
        v -= 1
        precedence.append((u, v))
        precedence_graph[u].append(v)
        rev_graph[v].append(u)

    task_duration = list(map(int, input().split()))
    num_team = int(input())
    s = list(map(int, input().split()))

    K = int(input())
    cost = defaultdict(dict)
    can_do = [0] * num_task

    for _ in range(K):
        i, j, w = map(int, input().split())
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


def greedy_construct(problem):
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


def decode_state(cur_state, problem):
    task_End = [0] * problem.num_task
    teamAvaiable = problem.s[:]
    schedule = []

    task_order, team_assignment = cur_state.task_order, cur_state.team_assignment
    
    for currentTask, team in zip(task_order, team_assignment):
        pred_finish = 0
        for p in problem.rev_graph[currentTask]:
            if task_End[p] > pred_finish:
                pred_finish = task_End[p]
        
        earliest = max(teamAvaiable[team], pred_finish)
        teamAvaiable[team] = earliest + problem.duration[currentTask]
        task_End[currentTask] = earliest + problem.duration[currentTask]
        schedule.append((currentTask, team, earliest))
    
    return schedule


def calc_fitness(cur_state, problem):

    schedule = decode_state(cur_state, problem)
    finish_task, completion, totalCost = 0, 0, 0

    for task, team, start in schedule:
        finish_task += 1
        finish = start + problem.duration[task]
        if finish > completion:
            completion = finish
        totalCost += problem.cost[task][team] 

    return (problem.num_task - finish_task, completion, totalCost)


def is_precedence_feasible(task_order, problem):
    pos = {task: idx for idx, task in enumerate(task_order)}
    for (i, j) in problem.precedence:
        if i in pos and j in pos:
            if pos[i] >= pos[j]:
                return False
    return True
