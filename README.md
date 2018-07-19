<img src="logo.png" height="160px" align="right" />

# Hammlet

**H**ybridiz**a**tion **M**odels **M**aximum **L**ikelihood **E**stima**t**or

## Requirements

* Python 3.3+ or 2.7
* NumPy
* SciPy
* click
* colorama (on Windows)

## Installation

Simply use [pip](https://pip.pypa.io/en/stable/quickstart/):

    git clone https://github.com/ctlab/hammlet
    cd hammlet
    pip install .

## Usage

<details>
<summary>**`hammlet --help`**</summary>

    Usage: hammlet [OPTIONS]

      Hybridization Models Maximum Likelihood Estimator

      Author: Konstantin Chukharev (lipen00@gmail.com)

    Options:
      --preset <preset>              Preset data (laur/hctm/12-200/12-200-70-50/5-10/...)
      -i, --input <path|->           File with markers presence/absence data
      -n, --names <name...>          Space-separated list of four species names
      -y <int...>                    Space-separated list of ten y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)
      -r <float...>                  Space-separated list of four r values  [default: 1, 1, 1, 1]
      -m, --model <name...|all>      Comma-separated list of models
      --chain [H1|H2]                Model group for simplest models computation
      --best <int|all>               Number of best models to show  [default: all]
      --method [SLSQP|L-BFGS-B|TNC]  Optimization method  [default: SLSQP]
      --theta0 <n0 T1 T3 g1 g3>      Space-separated list of five initial theta components (n0 T1 T3 gamma1 gamma3)
      --only-first                   Do calculations only for first (initial) permutation
      --only-permutation <name...>   Do calculations only for given permutation
      --free-permutation             [chain] Use best permutations for each simpler model
      --only-a                       Do only a_ij calculations
      --no-polytomy                  Do not show polytomy results
      --show-permutation <name...>   Show morphed y values for given permutation
      -p, --pvalue <float>           p-value for statistical tests  [default: 0.05]
      --debug                        Debug.
      --version                      Show the version and exit.
      -h, --help                     Show this message and exit.

</details>

### Use cases

Hammlet can be used to do following things:

* Calculate a_ij values for specified hybridization models

    <details>
    <summary>**`hammlet --only-a -m 2H1`**</summary>

        [*] Doing only a_ij calculations...
        [+] Result for model 2H1, permutation [A, B, C, D], theta=(96.0, 0.5, 0.5, 0.5, 0.5), r=(1, 1, 1, 1):
         ij  y_ij ~ij~~y_ij~  a_ij
         11   16   11   16   32.178
         12   16   12   16   28.728
         13   16   13   16   43.413
         14   16   14   16   11.231
         22   16   22   16   18.269
         23   16   23   16    9.322
         24   16   24   16   25.140
         33   16   33   16   10.862
         34   16   34   16    8.546
         44   16   44   16    7.044

    </details>

* Optimize model parameters to maximize likelihood for all possible permutations (reorderings) of species
    <details>
    <summary>**`hammlet --preset laur -m 2H1 --best 3`**</summary>

        [*] Using preset "laur"
        [*] Species: Dog, Cow, Horse, Bat
        [*] y values: 22 21 7 11 14 12 18 16 17 24
        [*] Optimizing model 2H1...
        [+] Done optimizing model 2H1 in 0.4 s.
        [@] 2H1, TTgg, 1, Cow, Bat, Dog, Horse, LL=292.589, n0=95.495, T1=0.150, T3=0.077, g1=1.000, g3=0.533
        [@] 2H1, TTgg, 2, Dog, Bat, Cow, Horse, LL=292.414, n0=95.447, T1=0.175, T3=0.040, g1=0.917, g3=0.572
        [@] 2H1, TTgg, 3, Bat, Dog, Horse, Cow, LL=292.327, n0=95.717, T1=0.177, T3=0.000, g1=0.468, g3=0.114
        [+] All done in 0.4 s.

    </details>

* Optimize a group of models and infer chains of simpler models having insignificantly lower (worse) likelihood
    <details>
    <summary>**`hammlet --preset 12-200 --chain H1`**</summary>

        [*] Using preset "12-200"
        [*] Species: A, B, C, D
        [*] y values: 12 12 200 12 12 12 12 12 12 12
        [*] Searching for simplest models from H1...
        [*] Total 3 chain(s):
            2H1 -> 1PH1
            2H1 -> 1H2 -> 1PH1
            2H1 -> 1H3 -> 1PH1
        [+] Done calculating 1 simplest model(s) in 0.8 s.
        [@] 1PH1, 0TNg, 1, A, C, B, D, LL=965.392, n0=132.076, T1=0.000, T3=1.425, g1=0.000, g3=0.935
        [+] All done in 6.7 s.

    </details>

### Input

* As input, Hammlet requires two things – four _species names_ and ten _y values_

    - Pass them directly using `-n/--names` and `-y`:<br>
        `hammlet --names Dog Cow Horse Bat -y 22 21 7 11 14 12 18 16 17 24 ...`

    - or specify a file (or `-` for stdin) with a table using `-i/--input`:<br>
        `hammlet --input data/data_laurasiatherian ...`

    - or simply use one of the built-in presets using `--preset`:<br>
        `hammlet --preset laur ...`

* Also, Hammlet requires a _model(s)_ to be specified

    - Pass them by name using `-m/--model`:<br>
        `hammlet ... -m 2H1`<br>
        `hammlet ... -m 1H2,1T2A,1T1,PL1`

    - or use model _groups_ (currently, two groups are available: H1 and H2):<br>
        `hammlet ... -m H1,H2`

    - or simply use all models:<br>
        `hammlet ... -m all`

<details>
<summary>Presets</summary>

|    Preset    |       Species names       |            y values            |
|:------------:|:-------------------------:|:------------------------------:|
|     laur     |     Dow Cow Horse Bat     |  22 21 7 11 14 12 18 16 17 24  |
|     hctm     | Human Colugo Tupaia Mouse |    10 8 7 4 21 7 2 39 30 28    |
|    12-200    |          A B C D          | 12 12 200 12 12 12 12 12 12 12 |
| 12-200-70-50 |          A B C D          | 12 200 12 70 12 12 12 50 12 12 |
|     5-10     |          A B C D          |  5 10 59 3 5 20 68 125 72 10   |

</details>

<details>
<summary>Models parameters (bounds)</summary>

| Name  | Mnemo | T1  | T3  | g1  | g3  |     | Name  | Mnemo | T1  | T3  | g1  | g3  |
|:-----:|:-----:|:---:|:---:|:---:|:---:|:---:|:-----:|:-----:|:---:|:---:|:---:|:---:|
|  2H1  | TTgg  |     |     |     |     |     |  2H2  | TTgg  |     |     |     |     |
|  1H1  | TTg0  |     |     |     |     |     | 2HA1  | TTg0  |     |     |     |     |
|  1H2  | TT1g  |     |     |  1  |  1  |     | 2HA2  | TTg1  |     |     |     |     |
|  1H3  | TT0g  |     |     |  0  |  0  |     | 2HB1  | TT0g  |     |     |  0  |  0  |
|  1H4  | TTg1  |     |     |     |     |     | 2HB2  | TT1g  |     |     |  1  |  1  |
|  1HP  | T0gg  |     |  0  |     |     |     |  2HP  | T0gg  |     |  0  |     |     |
|  1T1  | TT10  |     |     |  1  |  1  |     |  2T1  | TT01  |     |     |  0  |  0  |
|  1T2  | TT00  |     |     |  0  |  0  |     |  2T2  | TT00  |     |     |  0  |  0  |
| 1T2A  | TT01  |     |     |  0  |  0  |     | 2T2A  | TT01  |     |     |  0  |  0  |
| 1T2B  | TT11  |     |     |  1  |  1  |     | 2T2B  | TT11  |     |     |  1  |  1  |
| 1PH1  | 0TNg  |  0  |     | N/D | N/D |     | 2PH1  | 0TNg  |  0  |     | N/D | N/D |
| 1PH1A | T01g  |     |  0  |  1  |  1  |     | 2PH2  | T0g0  |     |  0  |     |     |
| 1PH2  | T0g0  |     |  0  |     |     |     | 2PH2A | T00g  |     |  0  |  0  |  0  |
| 1PH3  | T0g1  |     |  0  |     |     |     | 2PH2B | T01g  |     |  0  |  1  |  1  |
|  1P1  | 0TN0  |  0  |     | N/D | N/D |     | 2PH2C | T0g1  |     |  0  |     |     |
|  1P2  | T00N  |     |  0  |  0  |  0  |     |  2P1  | 0TN0  |  0  |     | N/D | N/D |
| 1P2A  | 0TN1  |  0  |     | N/D | N/D |     | 2P1A  | 0TN1  |  0  |     | N/D | N/D |
| 1P2B  | T011  |     |  0  |  1  |  1  |     |  2P2  | T000  |     |  0  |  0  |  0  |
|  1P3  | T010  |     |  0  |  1  |  1  |     | 2P2A  | T011  |     |  0  |  1  |  1  |
|  PL1  | 00NN  |  0  |  0  | N/D | N/D |     |  2P3  | T010  |     |  0  |  1  |  1  |
|  PL2  | 00NN  |  0  |  0  | N/D | N/D |     | 2P3A  | T001  |     |  0  |  0  |  0  |

</details>

### Output

* To show only few best permutations among 24 possible use `--best <int>` option

* To suppress polytomy results (T1=T3=g1=g3 &asymp; 0) use `--no-polytomy` flag

## Testing

* To run available tests simply execute `pytest`

* If `pytest` is not available, command `python setup.py test` will bootstrap it for you
