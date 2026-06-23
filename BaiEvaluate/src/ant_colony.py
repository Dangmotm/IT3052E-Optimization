import time
import random

try:
    from .base import State, read_input, decode_state, load_algorithm_config
except ImportError:
    from base import State, read_input, decode_state, load_algorithm_config


class ACO:
    def __init__(self, problem, config):
        self.problem = problem
        self.max_time = float(config.max_time)
        self.num_ants = int(config.num_ants)
        self.alpha = float(config.alpha)
        self.beta = float(config.beta)
        self.rho = float(config.rho)
        self.tau0 = float(config.tau0)
        self.tau_min = float(config.tau_min)
        self.tau_max = float(config.tau_max)

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

    def init_pheromone(self):
        tau = {}
        for task in self.problem.schedulable_order:
            tau[task] = {team: self.tau0 for team in self.problem.available_team[task]}
        return tau

    def ant_construct(self, tau, alpha, beta):
        problem = self.problem
        task_End = [0] * problem.num_task
        teamAvaiable = problem.s[:]
        task_order = []
        team_assignment = []

        for currentTask in problem.schedulable_order:
            pred_finish = 0
            for p in problem.rev_graph[currentTask]:
                if pred_finish < task_End[p]:
                    pred_finish = task_End[p]

            # Compute weight for each available team
            weights = []
            teams = problem.available_team[currentTask]
            for team in teams:
                earliest = max(teamAvaiable[team], pred_finish)
                finish = earliest + problem.duration[currentTask]
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
            task_End[currentTask] = earliest + problem.duration[currentTask]
            teamAvaiable[chosen_team] = task_End[currentTask]
            task_order.append(currentTask)
            team_assignment.append(chosen_team)

        return State(task_order, team_assignment)

    def evaporate(self, tau, rho):
        for task in tau:
            for team in tau[task]:
                tau[task][team] *= (1.0 - rho)
                tau[task][team] = max(self.tau_min, tau[task][team])

    def deposit(self, tau, sol, fitness):
        _, completion, _ = fitness
        delta = 1.0 / (completion + 1)
        for task, team in zip(sol.task_order, sol.team_assignment):
            tau[task][team] += delta
            tau[task][team] = min(self.tau_max, tau[task][team])

    def solve(self):
        start_time = time.time()
        max_time = self.max_time
        num_ants = self.num_ants
        alpha = self.alpha
        beta = self.beta
        rho = self.rho
        ant_construct = self.ant_construct
        calc_fitness = self.calc_fitness
        evaporate = self.evaporate
        deposit = self.deposit
        current_time = time.time

        # Khởi tạo pheromone
        tau = self.init_pheromone()

        # Seed bằng greedy solution
        best = self.greedy_construct()
        f_best = calc_fitness(best)

        # Deposit pheromone từ greedy solution ban đầu
        deposit(tau, best, f_best)

        while True:
            elapsed = current_time() - start_time
            if elapsed >= max_time:
                break

            # Mỗi kiến xây một solution
            iteration_best = None
            f_iteration_best = None

            for _ in range(num_ants):
                ant_sol = ant_construct(tau, alpha, beta)
                f_ant = calc_fitness(ant_sol)

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

        return best


def main():
    problem = read_input()
    config, seed = load_algorithm_config("ACO")
    random.seed(seed)
    best = ACO(problem, config).solve()
    schedule = decode_state(best, problem)
    schedule.sort()
    print(len(problem.schedulable_order))
    for task, team, start in schedule:
        print(task + 1, team + 1, start)


if __name__ == "__main__":
    main()
