# IT3052E Optimization

Project gồm ba phần:

- `BaiNop`: source code chính dùng để nộp cho giảng viên hoặc trình chấm.
- `BaiEvaluate`: chương trình chạy testcase, tính score, đo runtime và ghi log.
- `Slide`: slide và tài liệu môn học trên lớp.

## Cấu trúc thư mục

```text
.
├── BaiNop
│   ├── AntColonyOptimization.py
│   ├── GeneticAlgorithm.py
│   ├── SimulatedAnnealing.py
│   └── TabuSearch.py
├── BaiEvaluate
│   ├── cfg
│   │   └── config.yaml
│   ├── data
│   │   ├── testcase1
│   │   │   └── task.inp
│   │   └── ...
│   ├── src
│   │   ├── ant_colony.py
│   │   ├── base.py
│   │   ├── genetic_algorithm.py
│   │   ├── simulated_annealing.py
│   │   └── tabu_search.py
│   ├── utils
│   │   ├── evaluator.py
│   │   └── logger.py
│   ├── main.py
│   └── requirements.txt
├── Slide
│   └── ...
└── README.md
```

## 1. Thư mục `BaiNop`

Đây là source code dùng để nộp.

Mỗi file là một chương trình Python độc lập:

- Đọc dữ liệu bằng `input()`.
- Không cần Hydra hoặc thư viện ngoài.
- Chỉ in nghiệm theo định dạng yêu cầu của đề bài.

Các thuật toán:

| File | Thuật toán |
|---|---|
| `AntColonyOptimization.py` | Ant Colony Optimization |
| `GeneticAlgorithm.py` | Genetic Algorithm |
| `SimulatedAnnealing.py` | Simulated Annealing |
| `TabuSearch.py` | Tabu Search |

### Chạy bằng cách nhập input trực tiếp

```powershell
cd BaiNop
python SimulatedAnnealing.py
```

Sau đó nhập hoặc dán dữ liệu input vào terminal.

### Chạy với testcase có sẵn

Từ thư mục gốc project:

```powershell
Get-Content BaiEvaluate\data\testcase1\task.inp | python BaiNop\SimulatedAnnealing.py
Get-Content BaiEvaluate\data\testcase1\task.inp | python BaiNop\TabuSearch.py
Get-Content BaiEvaluate\data\testcase1\task.inp | python BaiNop\GeneticAlgorithm.py
Get-Content BaiEvaluate\data\testcase1\task.inp | python BaiNop\AntColonyOptimization.py
```

Khi nộp trình chấm, sử dụng file tương ứng trong `BaiNop`.

## 2. Thư mục `BaiEvaluate`

Thư mục này dùng để:

- Chạy một hoặc nhiều thuật toán trên các testcase có sẵn.
- Tính score.
- Đo runtime thực tế.
- Ghi kết quả vào file JSONL.

Code trong `BaiEvaluate/src` là phiên bản tổ chức theo class để
`Evaluator` có thể import và chạy từng thuật toán.

### Cài đặt

```powershell
cd BaiEvaluate
python -m pip install -r requirements.txt
```

Các thư viện chính:

- Hydra
- OmegaConf

### Chạy toàn bộ

Đứng trong thư mục `BaiEvaluate`:

```powershell
python main.py
```

Mặc định chương trình chạy bốn thuật toán trên những testcase được khai báo
trong `cfg/config.yaml`.

### Chạy một thuật toán trên một testcase

```powershell
python main.py "test=[1]" only=SA
python main.py "test=[1]" only=TS
python main.py "test=[1]" only=GA
python main.py "test=[1]" only=ACO
```

### Chạy một thuật toán trên nhiều testcase

```powershell
python main.py "test=[1,2,3]" only=SA
```

### Chạy cả bốn thuật toán trên một testcase

```powershell
python main.py "test=[1]" only=null
```

### Thay đổi tham số tạm thời

Hydra cho phép override tham số mà không sửa `config.yaml`.

Ví dụ giới hạn SA trong 10 giây:

```powershell
python main.py "test=[1]" only=SA algorithm.SA.max_time=10
```

Ví dụ thay đổi population size của GA:

```powershell
python main.py "test=[1]" only=GA algorithm.GA.population_size=20
```

## Score

Evaluator trả về score theo thứ tự:

```text
(số task làm được, thời gian hoàn thành, tổng chi phí)
```

Ví dụ:

```text
(5, 235, 145)
```

Trong đó:

- `5`: số task làm được.
- `235`: thời gian hoàn thành.
- `145`: tổng chi phí.

## Runtime và log

`max_time` trong `config.yaml` là giới hạn thời gian tối đa của thuật toán.

Runtime trong log là thời gian chạy thực tế do `Evaluator` đo:

```python
start = time.time()
solution = solver.solve()
end = time.time()
runtime = end - start
```

Kết quả được ghi tại:

```text
BaiEvaluate/results/log.jsonl
```

Ví dụ:

```json
{
  "test": "test1",
  "SA": {
    "score": [5, 235, 145],
    "runtime": 10.000123500823975
  }
}
```

Tuple score được chuyển thành list khi ghi dưới định dạng JSON.

## Cấu hình evaluate

File cấu hình:

```text
BaiEvaluate/cfg/config.yaml
```

Các trường chính:

```yaml
seed: 42
only: null

test:
  - 1
  - 2
  - 3

methods:
  - ACO
  - GA
  - SA
  - TS
```

- `seed`: seed cho các thao tác random.
- `test`: danh sách testcase cần chạy.
- `methods`: danh sách thuật toán.
- `only: null`: chạy tất cả thuật toán.
- `only: SA`: chỉ chạy SA.

Tham số riêng nằm trong:

```yaml
algorithm:
  ACO:
    ...
  GA:
    ...
  SA:
    ...
  TS:
    ...
```

## Thêm testcase evaluate

Project không tự sinh testcase.

Để thêm testcase mới:

1. Tạo thư mục `BaiEvaluate/data/testcaseN`.
2. Đặt input tại `BaiEvaluate/data/testcaseN/task.inp`.
3. Thêm số `N` vào danh sách `test` trong `BaiEvaluate/cfg/config.yaml`.

## 3. Thư mục `Slide`

Thư mục `Slide` chứa slide và tài liệu được cung cấp trên lớp, bao gồm các
chủ đề như:

- Convex Optimization
- Dynamic Programming
- Linear Programming
- Branch and Bound
- Integer Programming
- Constraint Programming
- Heuristic và Metaheuristic

Các file trong thư mục này là tài liệu học tập, không phải source code chạy
thuật toán.
"# IT3052E-Optimization" 
