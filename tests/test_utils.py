from hammlet.utils import get_paths
from hammlet.models import models_hierarchy


def test_get_paths_H1_free():
    assert all(path[-1] == 'PL1' for path in get_paths('2H1', models_hierarchy['H1']['free']))


def test_get_paths_H1_nonfree():
    assert all(path[-1] == 'PL1' for path in get_paths('2H1', models_hierarchy['H1']['non-free']))


def test_get_paths_H2_free():
    assert all(path[-1] == 'PL2' for path in get_paths('2H2', models_hierarchy['H2']['free']))


def test_get_paths_H2_nonfree():
    assert all(path[-1] == 'PL2' for path in get_paths('2H2', models_hierarchy['H2']['non-free']))
