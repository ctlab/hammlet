# HMMLE

Hybridization Models Maximum Likelihood Estimator

## Requirements

* **Python 3.6**
* numpy
* scipy
* click
* colorama

## Installation

`pip install git+https://github.com/ctlab/hmmle`

or

```sh
git clone https://github.com/ctlab/hmmle
cd hmmle
python setup.py install
```

# Usage

`hmmle --help`

## Input

* Input can be either:
    - a _file_ with markers presense/absence data using `-i/--input`:
    ```
    hmmle --input data/data_laurasiatherian
    ```

    - or a directly passed _names_ and $y_{ij}$ values using `--names` and `-y`:
    ```
    hmmle --names Dog Cow Horse Bat -y 17 18 12 11 7 21 24 16 14 22
    ```

* Pass `-` instead of filename to read data from _stdin_:
    ```
    cat data/data_laurasiatherian | hmmle -i -
    ```

## Output

* To show only few best permutations among 24 possible use `--best`:
    ```
    hmmle -i data/data_laurasiatherian -m 2H1 --best 3
    ```

## Calculations

* To select which models to optimize use `-m/--model`:
    ```
    hmmle -i data/data_laurasiatherian --model 2H1 --best 3
    hmmle -i data/data_laurasiatherian -m 2H1 -m 1P1 -m 1P2 --best 1
    ```

* To set up $r$ values use `-r`:
    ```
    hmmle -i data/data_laurasiatherian -r 0.5 0.4 0.8 0.6
    ```

* To set up initial values for $\theta$ components ($n_0, T_1, T_3, \gamma_1, \gamma_3$) use `--theta0`:
    ```
    hmmle -i data/data_laurasiatherian -m 2H2 --best 3 --theta0 85 0.4 0.5 0.8 0.2
    ```

* To make only $a_{ij}$ calculations for given $\theta_0$ and $r$ without further optimization use `--only-a`:
    ```
    hmmle -i data/data_laurasiatherian -m 2H1 --theta0 100 0.9 1.25 0.3 0.6 --only-a
    ```

* To make optimizations only for first permutation use `--only-first`:
    ```
    hmmle -i data/data_laurasiatherian -m 2H1 --only-first
    ```

# Test:

* Tests are not implemented yet, but you can check that everything is working with `--test` switch.
In this mode tool uses some [predefined data](data/data_laurasiatherian) and optimizes all 22 models.
    ```
    hmmle --test --best 1
    ```
