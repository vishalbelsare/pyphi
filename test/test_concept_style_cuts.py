import pytest
import numpy as np

from pyphi import config, compute
from pyphi.constants import Direction
from pyphi.compute import concept_cuts, ConceptStyleSystem, BigMipConceptStyle
from pyphi.models import KCut, KPartition, Part
from test_models import bigmip


@pytest.fixture()
def kcut_past():
    partition = KPartition(Part((0, 2), (0,)), Part((), (2,)), Part((3,), (3,)))
    return KCut(Direction.PAST, partition)


@pytest.fixture()
def kcut_future():
    partition = KPartition(Part((0, 2), (0,)), Part((), (2,)), Part((3,), (3,)))
    return KCut(Direction.FUTURE, partition)


def test_cut_indices(kcut_past, kcut_future):
    assert kcut_past.indices == (0, 2, 3)
    assert kcut_future.indices == (0, 2, 3)


def test_apply_cut(kcut_past, kcut_future):
    cm = np.ones((4, 4))
    cut_cm = np.array([
        [1, 1, 1, 0],
        [1, 1, 1, 1],
        [0, 1, 0, 0],
        [0, 1, 0, 1]])
    assert np.array_equal(kcut_past.apply_cut(cm), cut_cm)

    cm = np.ones((4, 4))
    cut_cm = np.array([
        [1, 1, 0, 0],
        [1, 1, 1, 1],
        [1, 1, 0, 0],
        [0, 1, 0, 1]])
    assert np.array_equal(kcut_future.apply_cut(cm), cut_cm)


def test_cut_matrix(kcut_past, kcut_future):
    assert np.array_equal(kcut_past.cut_matrix(4), np.array([
        [0, 0, 0, 1],
        [0, 0, 0, 0],
        [1, 0, 1, 1],
        [1, 0, 1, 0]]))

    assert np.array_equal(kcut_future.cut_matrix(4), np.array([
        [0, 0, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 1, 1],
        [1, 0, 1, 0]]))


def test_splits_mechanism(kcut_past):
    assert kcut_past.splits_mechanism((0, 3))
    assert kcut_past.splits_mechanism((2, 3))
    assert not kcut_past.splits_mechanism((0,))
    assert not kcut_past.splits_mechanism((3,))


def test_all_cut_mechanisms(kcut_past):
    assert kcut_past.all_cut_mechanisms() == (
        (2,), (0, 2), (0, 3), (2, 3), (0, 2, 3))


@config.override(PARTITION_TYPE='TRI')
def test_concept_style_cuts():
    assert list(concept_cuts(Direction.PAST, (0,))) == [
        KCut(Direction.PAST, KPartition(Part((), ()), Part((), (0,)),
                                        Part((0,), ())))]

    assert list(concept_cuts(Direction.FUTURE, (0,))) == [
        KCut(Direction.FUTURE, KPartition(Part((), ()), Part((), (0,)),
                                        Part((0,), ())))]


def test_kcut_equality(kcut_past, kcut_future):
    other = KCut(Direction.PAST, KPartition(Part((0, 2), (0,)), Part((), (2,)),
                                            Part((3,), (3,))))
    assert kcut_past == other
    assert hash(kcut_past) == hash(other)
    assert hash(kcut_past) != hash(kcut_past.partition)

    assert kcut_past != kcut_future
    assert hash(kcut_past) != hash(kcut_future)


def test_system_accessors(s):
    cut_past = KCut(Direction.PAST, KPartition(Part((0, 2), (0, 1)),
                                               Part((1,), (2,))))
    cs_past = ConceptStyleSystem(s, Direction.PAST, cut_past)
    assert cs_past.cause_system.cut == cut_past
    assert cs_past.effect_system.cut == s.null_cut

    cut_future = KCut(Direction.FUTURE, KPartition(Part((0, 2), (0, 1)),
                                                   Part((1,), (2,))))
    cs_future = ConceptStyleSystem(s, Direction.FUTURE, cut_future)
    assert cs_future.cause_system.cut == s.null_cut
    assert cs_future.effect_system.cut == cut_future


def big_mip_cs(phi=1.0, subsystem=None):
    return BigMipConceptStyle(
        subsystem=subsystem,
        mip_past=bigmip(subsystem=subsystem, phi=phi),
        mip_future=bigmip(subsystem=subsystem, phi=phi))


def test_big_mip_concept_style_ordering(s, subsys_n0n2, s_noised):
    assert big_mip_cs(subsystem=s) == big_mip_cs(subsystem=s)
    assert big_mip_cs(phi=1, subsystem=s) < big_mip_cs(phi=2, subsystem=s)
    assert big_mip_cs(subsystem=s) >= big_mip_cs(subsystem=subsys_n0n2)

    with pytest.raises(TypeError):
        big_mip_cs(subsystem=s) < big_mip_cs(subsystem=s_noised)


@config.override(SYSTEM_CUTS='CONCEPT_STYLE', PARALLEL_CUT_EVALUATION=True)
def test_unpickling_in_parallel_computations(s, flushcache, restore_fs_cache):
    assert compute.big_phi(s) == 0.6875
