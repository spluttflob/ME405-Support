"""!
@file task_share.py
This file contains classes which allow tasks to share data without the risk
of data corruption by interrupts. 

@author JR Ridgely
@date   2017-Jan-01 JRR Approximate date of creation of file
@date   2021-Dec-18 JRR Docstrings changed to work without DoxyPyPy
@copyright This program is copyright (c) 2017-2021 by JR Ridgely and released
           under the GNU Public License, version 3.0. 
"""

import array
import gc
import pyb
import micropython


## This is a system-wide list of all the queues and shared variables. It is
#  used to create diagnostic printouts. 
share_list = []

## This dictionary allows readable printouts of queue and share data types.
type_code_strings = {'b' : "int8",   'B' : "uint8",
                     'h' : "int16",  'H' : "uint16",
                     'i' : "int(?)", 'I' : "uint(?)",
                     'l' : "int32",  'L' : "uint32",
                     'q' : "int64",  'Q' : "uint64",
                     'f' : "float",  'd' : "double"}


def show_all ():
    """!
    Create a string holding a diagnostic printout showing the status of
    each queue and share in the system. 
    @return A string containing information about each queue and share
    """
    gen = (str (item) for item in share_list)
    return '\n'.join (gen)


# ============================================================================

class BaseShare:
    """!
    Base class for queues and shares which exchange data between tasks.
    
    One should never create an object from this class; it doesn't do anything
    useful. It exists to implement things which are common between its child
    classes @c Queue and @c Share. 
    """

    def __init__ (self, type_code, thread_protect = True, name = None):
        """!
        Create a base queue object when called by a child class initializer.

        This method creates the things which queues and shares have in common.
        """
        self._type_code = type_code
        self._thread_protect = thread_protect

        # Add this queue to the global share and queue list
        share_list.append (self)


# ============================================================================

class Queue (BaseShare):
    """!
    A queue which is used to transfer data from one task to another.

    If parameter 'thread_protect' is @c True when a queue is created, transfers
    of data will be protected from corruption in the case that one task might
    interrupt another due to use in a pre-emptive multithreading environment or
    due to one task being run as an interrupt service routine.

    An example of the creation and use of a queue is as follows:

    @code
    import task_share

    # This queue holds unsigned short (16-bit) integers
    my_queue = task_share.Queue ('H', 100, name="My Queue")

    # Somewhere in one task, put data into the queue
    my_queue.put (some_data)

    # In another task, read data from the queue
    something = my_queue.get ()
    @endcode
    """
    ## A counter used to give serial numbers to queues for diagnostic use.
    ser_num = 0

    def __init__ (self, type_code, size, thread_protect = True, 
                  overwrite = False, name = None):
        """!
        Initialize a queue object to carry and buffer data between tasks.

        This method sets up a queue by allocating memory for the contents and 
        setting up the components in an empty configuration. 

        Each queue can only carry data of one particular type which must be
        chosen from the following list. The data type is specified by a 
        one-letter type code which is given as for the Python @c array.array
        type, which can be any of the following:
        |      |      |      |
        |:-----|:-----|:-----|
        | **b** (signed char) | **B** (unsigned char) | 8 bit integers |
        | **h** (signed short) | **H** (unsigned short) | 16 bit integers |
        | **i** (signed int) | **I** (unsigned int) | 32 bit integers (probably) |
        | **l** (signed long) | **L** (unsigned long) | 32 bit integers |
        | **q** (signed long long) | **Q** (unsigned long long) | 64 bit integers |
        | **f** (float) | **d** (double-precision float) | |

        @param type_code The type of data items which the queue can hold
        @param size The maximum number of items which the queue can hold
        @param thread_protect @c True if mutual exclusion protection is used
        @param overwrite If @c True, oldest data will be overwritten with new
               data if the queue becomes full 
        @param name A short name for the queue, default @c QueueN where @c N
               is a serial number for the queue

        """
        # First call the parent class initializer
        super ().__init__ (type_code, thread_protect, name)

        self._size = size
        self._overwrite = overwrite
        self._name = str (name) if name != None \
            else 'Queue' + str (Queue.ser_num)
        Queue.ser_num += 1

        # Allocate memory in which the queue's data will be stored
        try:
            self._buffer = array.array (type_code, range (size))
        except MemoryError:
            self._buffer = None
            raise
        except ValueError:
            self._buffer = None
            raise

        # Initialize pointers to be used for reading and writing data
        self.clear ()

        # Since we may have allocated a bunch of memory, call the garbage
        # collector to neaten up what memory is left for future use
        gc.collect ()


    @micropython.native
    def put (self, item, in_ISR = False):
        """!
        Put an item into the queue.

        If there isn't room for the item, wait (blocking the calling process)
        until room becomes available, unless the @c overwrite constructor
        parameter was set to @c True to allow old data to be clobbered. If
        non-blocking behavior without overwriting is needed, one should call
        @c full() to ensure that the queue is not full before putting data
        into it:
        @code
        |   def some_task ():
        |       # Setup
        |       while True:
        |           if not my_queue.full ():
        |               my_queue.put (create_something_to_put ())
        |           yield 0
        @endcode
        @param item The item to be placed into the queue
        @param in_ISR Set this to @c True if calling from within an ISR
        """
        # If we're in an ISR and the queue is full and we're not allowed to
        # overwrite data, we have to give up and exit
        if self.full ():
            if in_ISR:
                return

            # Wait (if needed) until there's room in the buffer for the data
            if not self._overwrite:
                while self.full ():
                    pass

        # Prevent data corruption by blocking interrupts during data transfer
        if self._thread_protect and not in_ISR:
            _irq_state = pyb.disable_irq ()

        # Write the data and advance the counts and pointers
        self._buffer[self._wr_idx] = item
        self._wr_idx += 1
        if self._wr_idx >= self._size:
            self._wr_idx = 0
        self._num_items += 1
        if self._num_items >= self._size:        # Can't be fuller than full
            self._num_items = self._size
        if self._num_items > self._max_full:     # Record maximum fillage
            self._max_full = self._num_items

        # Re-enable interrupts
        if self._thread_protect and not in_ISR:
            pyb.enable_irq (_irq_state)


    @micropython.native
    def get (self, in_ISR = False):
        """!
        Read an item from the queue.

        If there isn't anything in there, wait (blocking the calling process)
        until something becomes available. If non-blocking reads are needed,
        one should call @c any() to check for items before attempting to read
        from the queue. This is usually done in a low priority task:
        @code
        |   def some_task ():
        |       # Setup
        |       while True:
        |           if my_queue.any ():
        |               something = my_queue.get ()
        |               do_something_with (something)
        |           # More loop stuff
        |           yield 0
        @endcode
        @param in_ISR Set this to @c True if calling from within an ISR
        """
        # Wait until there's something in the queue to be returned
        while self.empty ():
            pass

        # Prevent data corruption by blocking interrupts during data transfer
        if self._thread_protect and not in_ISR:
            irq_state = pyb.disable_irq ()

        # Get the item to be returned from the queue
        to_return = self._buffer[self._rd_idx]

        # Move the read pointer and adjust the number of items in the queue
        self._rd_idx += 1
        if self._rd_idx >= self._size:
            self._rd_idx = 0
        self._num_items -= 1
        if self._num_items < 0:
            self._num_items = 0

        # Re-enable interrupts
        if self._thread_protect and not in_ISR:
            pyb.enable_irq (irq_state)

        return (to_return)


    @micropython.native
    def any (self):
        """!
        Check if there are any items in the queue.

        Returns @c True if there are any items in the queue and @c False
        if the queue is empty.
        @return @c True if items are in the queue, @c False if not
        """
        return (self._num_items > 0)


    @micropython.native
    def empty (self):
        """!
        Check if the queue is empty.

        Returns @c True if there are no items in the queue and @c False if 
        there are any items therein.
        @return @c True if queue is empty, @c False if it's not empty
        """
        return (self._num_items <= 0)


    @micropython.native
    def full (self):
        """!
        Check if the queue is full.

        This method returns @c True if the queue is already full and there
        is no room for more data without overwriting existing data. 
        @return @c True if the queue is full
        """
        return (self._num_items >= self._size)


    @micropython.native
    def num_in (self):
        """!
        Check how many items are in the queue.

        This method returns the number of items which are currently in the 
        queue.
        @return The number of items in the queue
        """
        return (self._num_items)


    def clear (self):
        """!
        Remove all contents from the queue.
        """
        self._rd_idx = 0
        self._wr_idx = 0
        self._num_items = 0
        self._max_full = 0


    def __repr__ (self):
        """!
        This method puts diagnostic information about the queue into a string.

        It shows the queue's name and type as well as the maximum number of
        items and queue size. 
        """
        return ('{:<12s} Queue<{:s}> Max Full {:d}/{:d}'.format (self._name,
                type_code_strings[self._type_code], self._max_full, self._size))


# ============================================================================

class Share (BaseShare):
    """!
    An item which holds data to be shared between tasks.
    This class implements a shared data item which can be protected against
    data corruption by pre-emptive multithreading. Multithreading which can
    corrupt shared data includes the use of ordinary interrupts as well as the
    use of pre-emptive multithreading such as by a Real-Time Operating System
    (RTOS).
 
    An example of the creation and use of a share is as follows:
    @code
    import task_share

    # This share holds a signed short (16-bit) integer
    my_share = task_share.Queue ('h', name="My Share")

    # Somewhere in one task, put data into the share
    my_share.put (some_data)

    # In another task, read data from the share
    something = my_share.get ()
    @endcode
    """
    ## A counter used to give serial numbers to shares for diagnostic use.
    ser_num = 0


    def __init__ (self, type_code, thread_protect = True, name = None):
        """!
        Create a shared data item used to transfer data between tasks.

        This method allocates memory in which the shared data will be buffered.

        Each share can only carry data of one particular type which must be
        chosen from the following list. The data type is specified by a 
        one-letter type code which is given as for the Python @c array.array
        type, which can be any of the following:
        |      |      |      |
        |:-----|:-----|:-----|
        | **b** (signed char) | **B** (unsigned char) | 8 bit integers |
        | **h** (signed short) | **H** (unsigned short) | 16 bit integers |
        | **i** (signed int) | **I** (unsigned int) | 32 bit integers (probably) |
        | **l** (signed long) | **L** (unsigned long) | 32 bit integers |
        | **q** (signed long long) | **Q** (unsigned long long) | 64 bit integers |
        | **f** (float) | **d** (double-precision float) | |

        @param type_code The type of data items which the share can hold
        @param thread_protect True if mutual exclusion protection is used
        @param name A short name for the share, default @c ShareN where @c N
               is a serial number for the share
        """
        # First call the parent class initializer
        super ().__init__ (type_code, thread_protect, name)

        self._buffer = array.array (type_code, [0])

        self._name = str (name) if name != None \
            else 'Share' + str (Share.ser_num)
        Share.ser_num += 1


    @micropython.native
    def put (self, data, in_ISR = False):
        """!
        Write an item of data into the share.

        This method puts data into the share; any old data is overwritten.
        This code disables interrupts during the writing so as to prevent
        data corrupting by an interrupt service routine which might access
        the same data.
        @param data The data to be put into this share
        @param in_ISR Set this to True if calling from within an ISR
        """

        # Disable interrupts before writing the data
        if self._thread_protect and not in_ISR:
            irq_state = pyb.disable_irq ()

        self._buffer[0] = data

        # Re-enable interrupts
        if self._thread_protect and not in_ISR:
            pyb.enable_irq (irq_state)


    @micropython.native
    def get (self, in_ISR = False):
        """!
        Read an item of data from the share.

        If thread protection is enabled, interrupts are disabled during the time
        that the data is being read so as to prevent data corruption by changes
        in the data as it is being read. 
        @param in_ISR Set this to True if calling from within an ISR
        """
        # Disable interrupts before reading the data
        if self._thread_protect and not in_ISR:
            irq_state = pyb.disable_irq ()

        to_return = self._buffer[0]

        # Re-enable interrupts
        if self._thread_protect and not in_ISR:
            pyb.enable_irq (irq_state)

        return (to_return)


    def __repr__ (self):
        """!
        Puts diagnostic information about the share into a string.

        Shares are pretty simple, so we just put the name and type. 
        """
        return ("{:<12s} Share<{:s}>".format (self._name,
                type_code_strings[self._type_code]))


