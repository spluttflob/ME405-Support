"""!
@file doxybug.py
This file tries to reproduce a Doxygen bug which causes the class documentation
for the second class in a file to be used instead of the documentation for the
first method in the second class.
"""

class Alpha:
    """! The class documentation of the first class. """
    def __init__(self):
        """! The first class's initializer. """
    def moo(self):
        """! Perhaps make a bovine sound? """
        
class Beta:
    """! The class documentation of the second class. """
    def __init__(self):
        """! The second class's constructor. """
    def meow(self):
        """! Make a feline sound, but not purring. """
