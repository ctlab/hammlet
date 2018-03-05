<img src="logo.png" height="160px" align="right" />

# HaMMLEt

**H**ybridiz**a**tion **M**odels **M**aximum **L**ikelihood **E**stima**t**or

## Requirements

* Python 3.3+ or 2.7
* NumPy
* SciPy
* click
* colorama

## Installation

Install directly from github via pip:

```
pip install git+https://github.com/ctlab/hammlet
```

**or** clone and install via setuptools:

```sh
git clone https://github.com/ctlab/hammlet
cd hammlet
python setup.py install
```

## Usage

`hammlet --help`

### Input

* Input can be either:
    - a _file_ with markers presense/absence data using `-i/--input`:
    ```
    hammlet --input data/data_laurasiatherian
    ```

    - or a directly passed _names_ and y_ij values using `--names` and `-y`:
    ```
    hammlet --names Dog Cow Horse Bat -y 22 21 7 11 14 12 18 16 17 24
    ```

* Pass `-` instead of filename to read data from _stdin_:
    ```
    cat data/data_laurasiatherian | hammlet -i -
    ```

### Output

* To show only few best permutations among 24 possible use `--best`:
    ```
    hammlet -i data/data_laurasiatherian --best 3
    ```

* To make output less verbose use `--compact`:
    ```
    hammlet -i data/data_laurasiatherian --compact
    ```

* To suppress polytomy results (T1=T3=gamma1=gamma3=0) use `--no-polytomy`:
    ```
    hammlet -i data/data_laurasiatherian --compact --no-polytomy
    ```

### Calculations

* To select which models to optimize use `-m/--model`:
    ```
    hammlet -i data/data_laurasiatherian --model 2H1 --best 5
    hammlet -i data/data_laurasiatherian -m 2H1 -m 1P1 -m 1P2 --best 3
    hammlet -i data/data_laurasiatherian -m all --best 1
    ```

* To set up r values use `-r`:
    ```
    hammlet -i data/data_laurasiatherian -r 0.5 0.4 0.8 0.6
    ```

* To set up initial values for theta components (n0, T1, T3, gamma1, gamma3) use `--theta0`:
    ```
    hammlet -i data/data_laurasiatherian -m 2H2 --best 3 --theta0 85 0.4 0.5 0.8 0.2
    ```

* To make only a_ij calculations for given theta0 and r without further optimization use `--only-a`:
    ```
    hammlet -i data/data_laurasiatherian -m 2H1 --theta0 100 0.9 1.25 0.3 0.6 --only-a
    ```

* To make optimizations only for first permutation use `--only-first`:
    ```
    hammlet -i data/data_laurasiatherian -m 2H1 --only-first
    ```

## Test:

* Tests are not implemented yet, but you can check that everything is working with `--test` switch.
In this mode tool uses some [predefined data](data/data_laurasiatherian) and optimizes all 22 models.
    ```
    hammlet --test --best 1
    ```
