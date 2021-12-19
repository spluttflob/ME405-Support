"""!
@file the_answer.py
This file contains code which computes the answer to the question of Life, the
Universe, and Everything. Hopefully it can be done in fewer than 100,000 years.

TODO: Create a function which explains what the question actually means. This
      might take a bit longer. 

@author Spluttflob
@date   23-Dec-2258 SPL Original file
@copyright (c) 2258 by Nobody and released under the GNU Public License v3
"""

import math                  # We don't really need to; this is just an example

## This list of characters contains valuable information about the Universe
chars = ["arthur", "ford", "trillian", "zaphod", "marvin", "jeltz",
         "slartibartfast"]


def the_answer (two):
    """!
    Compute the answer to the ultimate question.
    This function computes the greatest answer of all answers using information
    of great relevance.
    @param   two An integer given to this function which really should be 2
    @returns The ultimate answer, as an integer
    """
    # Here's a variable which can only be used inside this function
    thou_shalt_count_to = 3

    # Notice the use of mathematical assignment operator *= below
    answer_this = len (chars) * thou_shalt_count_to
    answer_this *= two

    return answer_this


# The following code only runs if this file is run as the main script; it does
# not run if this file is imported as a module
if __name__ == "__main__":
    
    # One of several ways to print formatted lines in Python
    print ("The Answer is (spoiler alert): {:d}".format (the_answer (2)))
    
