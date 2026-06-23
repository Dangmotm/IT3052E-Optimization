import hydra
from omegaconf import DictConfig
from hydra.utils import to_absolute_path
from pathlib import Path

from utils.logger import Logger
from utils.evaluator import Evaluator


@hydra.main(version_base=None, config_path="cfg", config_name="config")
def main(cfg: DictConfig):
    L = Logger(to_absolute_path(cfg.path.RES))
    E = Evaluator()
    test = cfg.test

    for t in test:
        path = Path(to_absolute_path(cfg.path.DATA)) / f"testcase{t}" / "task.inp"
        cfg.current_test = f"test{t}"

        problem = E.read_input(path)
        name, results = E.evaluate(problem, cfg)

        L.log(name, results)

    print("[info] Done.")


if __name__ == "__main__":
    main()
