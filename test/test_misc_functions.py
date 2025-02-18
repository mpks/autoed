import pytest
import os
from autoed.utility.misc_functions import scrap


@pytest.fixture
def make_correct_scrap_file(scope='module'):

    test_file = 'scrap.txt'
    with open(test_file, 'w') as correct_file:

        correct_file.write('test_var = 2.05\n')
        correct_file.write('rotationSpeed = 2\n')
        correct_file.write('framerate = None\n')

    yield test_file

    os.remove(test_file)


def test_scrap_correct(make_correct_scrap_file):

    # Test regular case
    test_file = make_correct_scrap_file
    succes, value = scrap(test_file, 'rotationSpeed',
                          default_type=int, default_value=1)
    assert value == 2
    print('\nscrap: Regular case OK')

    # Test missing variable
    succes, value = scrap(test_file, 'some_fake_value',
                          default_type=int, default_value=-1)
    assert value == -1 and not succes
    print('scrap: Missing variable OK')
