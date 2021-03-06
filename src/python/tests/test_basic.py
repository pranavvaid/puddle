
import puddle
import pytest


@pytest.fixture(scope='function')
def session():

    with puddle.mk_session() as sess:
        yield sess


def test_easy(session):
    a = session.input((1,1), 1.0)
    b = session.input((3,3), 1.0)
    c = a.mix(b)

    droplets = session.droplets()

    # TODO droplet ids should be strings at some point
    assert set(droplets.keys()) == {c._id}


def test_consumed(session):

    a = session.input((1,1), 1.0)
    b = session.input((3,3), 1.0)
    c = a.mix(b)

    with pytest.raises(puddle.DropletConsumed):
        a.mix(b)


def test_volume(session):

    a = session.input((1,1), 1.0)
    b = session.input((3,3), 2.0)

    ab = session.mix(a, b)

    (a_split, b_split) = session.split(ab)

    assert session.droplets()[a_split._id]['volume'] == 1.5
    assert session.droplets()[b_split._id]['volume'] == 1.5
