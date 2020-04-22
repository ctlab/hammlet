from hammlet.models import models_hierarchy
from hammlet.utils import get_paths


def test_get_paths_H1_free():
    assert all(
        path[-1] == "P" for path in get_paths(models_hierarchy["H1"]["fixed"], "2H1")
    )


def test_get_paths_H1_nonfree():
    assert all(
        path[-1] == "P" for path in get_paths(models_hierarchy["H1"]["non-free"], "2H1")
    )


def test_get_paths_H2_free():
    assert all(
        path[-1] == "PL2" for path in get_paths(models_hierarchy["H2"]["fixed"], "2H2")
    )


def test_get_paths_H2_nonfree():
    assert all(
        path[-1] == "PL2"
        for path in get_paths(models_hierarchy["H2"]["non-free"], "2H2")
    )
