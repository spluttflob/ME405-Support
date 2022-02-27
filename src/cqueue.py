"""!
@file cqueue.py
This file contains documentation and a test program for the custom C queues
used in the ME405 library. These queues are faster than regular Python based
queues and don't allocate memory.

The code in this file is @b not the source code which makes the C queues work.
That code is written in C as the file @c cqueues.c and compiled into the
MicroPython image used in the ME405 course. 

@author JR Ridgely
@date   2022-Feb-24 JRR Original file
@copyright (c) 2022 by JR Ridgely and released under the GNU Public License V3.

It is intended for educational use only, but its use is not limited thereto.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

# Code in this section is never run; it's here to trick Doxygen into making
# documentation for the C code, whose Python programming interface cannot be
# directly documented by Doxygen.
if __name__ == "__not_me__":

    class FloatQueue:
        """!
        @brief   A fast, pre-allocated queue of floats for MicroPython.
        @details This class is written in C for speed. When a FloatQueue
                 object is created, memory is allocated to hold the given
                 number of items. Data is put into the queue with its put()
                 method, and the oldest available data is retrieved with the
                 get() method. Because running put() and get() doesn't
                 allocate any memory, it can be used in interrupt callbacks. 

                 When one creates a queue, one specifies the number of items
                 which can be stored at once in the queue. After creating a
                 queue, one writes items into a queue using its put() method.
                 Writing into a full queue causes the oldest data to be erased;
                 method full() can be used before writing to check for such a
                 problem. Reading from the queue is done by a call to get(),
                 which returns the oldest available data item or @c None if the
                 queue is empty:
                 @code
                 QUEUE_SIZE = 42
                 float_queue = cqueue.FloatQueue(QUEUE_SIZE)
                 for count in range(27):
                     float_queue.put(count)  # Or do this in interrupt callback
                 ...
                 while float_queue.any():
                     print(float_queue.get())
                 @endcode
        """

        def __init__(self, size : int):
            """!
            @brief   Create a fast queue for floats.
            @details When the queue is created, memory is allocated for the
                     given number of items. Putting items into the queue won't
                     cause new memory to be allocated, so the queue can be used
                     in interrupt callbacks and will run quickly.
            @param   size The maximum number of floats that the queue can hold
            """

        def any() -> bool:
            """!
            @brief   Checks if there are any items available in the queue.
            @returns @c True if there is at least one item in the queue,
                     @c False if not
            """

        def available() -> int:
            """!
            @brief   Checks how many items are available to be read from the
                     queue.
            @returns An integer containing the number of items in the queue
            """

        def put(data : float):
            """!
            @brief   Put a floating point number into the queue.
            @details If the queue is already full, the oldest data will be
                     overwritten. If this could cause problems, one can call
                     @c full() to check if the queue is already full before
                     writing the data.
            @param   data An integer to be put into the back of the queue
            """

        def get() -> float:
            """!
            @brief   Get an item from the queue if one is available.
            @details If the queue is empty, @c None will be returned.
            @returns The oldest float in the queue, or @c None if the queue
                     is currently empty.
            """

        def clear():
            """!
            @brief   Empty the queue.
            @details The pointers used to access data in the queue are reset to
                     their empty positions. The contents of the memory are not
                     changed and no new memory is allocated.
            """

        def full() -> bool:
            """!
            @brief   Check whether the queue is currently full.
            @details If the queue is full, writing new data will cause the
                     oldest data to be overwritten and lost. 
            @returns @c True if the queue is currently full or @c False if not
            """

        def max_full() -> int:
            """!
            @brief   Get the maximum number of unread items that have been in
                     the queue.
            @details This method returns the maximum number of items that have
                     been in the queue at any point since the queue was created
                     or cleared.
            @return  The maximum number of items that have been in the queue
            """


    class IntQueue:
        """!
        @brief   A fast, pre-allocated queue of integers for MicroPython.
        @details This class is written in C for speed. When an IntQueue
                 object is created, memory is allocated to hold the given
                 number of items. Data is put into the queue with its put()
                 method, and the oldest available data is retrieved with the
                 get() method. Because running put() and get() doesn't
                 allocate any memory, it can be used in interrupt callbacks.
                 
                 When one creates a queue, one specifies the number of items
                 which can be stored at once in the queue. After creating a
                 queue, one writes items into a queue using its put() method.
                 Writing into a full queue causes the oldest data to be erased;
                 method full() can be used before writing to check for such a
                 problem. Reading from the queue is done by a call to get(),
                 which returns the oldest available data item or @c None if the
                 queue is empty:
                 @code
                 QUEUE_SIZE = 42
                 int_queue = cqueue.IntQueue(QUEUE_SIZE)
                 for count in range(27):
                     int_queue.put(count)    # Or do this in interrupt callback
                 ...
                 while int_queue.any():
                     print(int_queue.get())
                 @endcode
        """

        def __init__(self, size : int):
            """!
            @brief   Create a fast queue for integers.
            @details When the queue is created, memory is allocated for the
                     given number of items. Putting items into the queue won't
                     cause new memory to be allocated, so the queue can be used
                     in interrupt callbacks and will run quickly.
            @param   size The maximum number of integers that the queue can
                     hold
            """

        def any() -> bool:
            """!
            @brief   Checks if there are any items available in the queue.
            @returns @c True if there is at least one item in the queue,
                     @c False if not
            """

        def available() -> int:
            """!
            @brief   Checks how many items are available to be read from the
                     queue.
            @returns An integer containing the number of items in the queue
            """

        def put(data : int):
            """!
            @brief   Put an integer into the queue.
            @details If the queue is already full, the oldest data will be
                     overwritten. If this could cause problems, one can call
                     @c full() to check if the queue is already full before
                     writing the data.
            @param   data An integer to be put into the back of the queue
            """

        def get() -> int:
            """!
            @brief   Get an item from the queue if one is available.
            @details If the queue is empty, @c None will be returned.
            @returns The oldest integer in the queue, or @c None if the queue
                     is currently empty.
            """

        def clear():
            """!
            @brief   Empty the queue.
            @details The pointers used to access data in the queue are reset to
                     their empty positions. The contents of the memory are not
                     changed and no new memory is allocated.
            """

        def full() -> bool:
            """!
            @brief   Check whether the queue is currently full.
            @details If the queue is full, writing new data will cause the
                     oldest data to be overwritten and lost. 
            @returns @c True if the queue is currently full or @c False if not
            """

        def max_full() -> int:
            """!
            @brief   Get the maximum number of unread items that have been in
                     the queue.
            @details This method returns the maximum number of items that have
                     been in the queue at any point since the queue was created
                     or cleared.
            @return  The maximum number of items that have been in the queue
            """

    class ByteQueue:
        """!
        @brief   A fast, pre-allocated queue of characters for MicroPython.
        @details Either bytes or Unicode (str) characters may be written into a
                 ByteQueue; only bytes will be stored and retrieved from it.
                 This class is written in C for speed. When a ByteQueue
                 object is created, memory is allocated to hold the given
                 number of items. Data is put into the queue with its put()
                 method, and the oldest available data is retrieved with the
                 get() method. Because running put() and get() doesn't
                 allocate any memory, it can be used in interrupt callbacks.
                 
                 When one creates a queue, one specifies the number of items
                 which can be stored at once in the queue. After creating a
                 queue, one writes items into a queue using its put() method.
                 Writing into a full queue causes the oldest data to be erased;
                 method full() can be used before writing to check for such a
                 problem. Reading from the queue is done by a call to get(),
                 which returns the oldest available data item or @c None if the
                 queue is empty:
                 @code
                 QUEUE_SIZE = 128
                 my_queue = cqueue.ByteQueue(QUEUE_SIZE)
                 for count in range(10):
                     my_queue.put(f"{count},", end="")
                 ...
                 while int_queue.any():
                     print(my_queue.get())
                 @endcode
        """

        def __init__(self, size : int):
            """!
            @brief   Create a fast queue for characters.
            @details When the queue is created, memory is allocated for the
                     given number of items. Putting items into the queue won't
                     cause new memory to be allocated, so the queue can be used
                     in interrupt callbacks and will run quickly.
            @param   size The maximum number of integers that the queue can
                     hold
            """

        def any() -> bool:
            """!
            @brief   Checks if there are any items available in the queue.
            @returns @c True if there is at least one item in the queue,
                     @c False if not
            """

        def available() -> int:
            """!
            @brief   Checks how many items are available to be read from the
                     queue.
            @returns An integer containing the number of items in the queue
            """

        def put(data : int):
            """!
            @brief   Put a character or string into the queue.
            @details If the queue is already full, the oldest data will be
                     overwritten. If this could cause problems, one can call
                     @c full() to check if the queue is already full before
                     writing the data.
            @param   data An integer to be put into the back of the queue
            """

        def get() -> int:
            """!
            @brief   Get an item from the queue if one is available.
            @details If the queue is empty, @c None will be returned.
            @returns The oldest character in the queue, or @c None if the queue
                     is currently empty.
            """

        def clear():
            """!
            @brief   Empty the queue.
            @details The pointers used to access data in the queue are reset to
                     their empty positions. The contents of the memory are not
                     changed and no new memory is allocated.
            """

        def full() -> bool:
            """!
            @brief   Check whether the queue is currently full.
            @details If the queue is full, writing new data will cause the
                     oldest data to be overwritten and lost. 
            @returns @c True if the queue is currently full or @c False if not
            """

        def max_full() -> int:
            """!
            @brief   Get the maximum number of unread items that have been in
                     the queue.
            @details This method returns the maximum number of items that have
                     been in the queue at any point since the queue was created
                     or cleared.
            @return  The maximum number of items that have been in the queue
            """


import utime
import cqueue

## The number of times to call put() for each queue
TEST_SIZE = 3000

## The number of elements in each queue which we create and test
NUM_QUEUE_SIZE = 2000

## The number of characters in the test byte queue
BYTE_QUEUE_SIZE = 20

## The number of times we try to put something into the byte queue. It's kept
#  somewhat small so we're putting in printable ASCII characters
BYTE_T_SIZE = 94

## The number of times we repeat the whole test
NUM_RUNS = 25

## The results of running tests repeatedly
overall = {"Int Sum"   : 0,
           "Int Max"   : 0,
           "Float Sum" : 0,
           "Float Max" : 0,
           "Byte Sum"  : 0,
           "Byte Max"  : 0
          }


def main():
    """!
    Run a test by creating queues, putting numbers into the queues, getting the
    numbers back out, and checking for consistency. While we're at it, keep
    track of the time it took to put things into the queues, as this can be
    important if putting data into a queue within an interrupt callback.
    """
    int_queue = cqueue.IntQueue(NUM_QUEUE_SIZE)
    float_queue = cqueue.FloatQueue(NUM_QUEUE_SIZE)
    byte_queue = cqueue.ByteQueue(BYTE_QUEUE_SIZE)

    intdursum = 0                        # Sums of durations of put() calls
    floatdursum = 0
    bytedursum = 0
    intdurmax = 0                        # Maximum durations of the put() calls
    floatdurmax = 0
    bytedurmax = 0

    # Write things into queues, overwriting some data to make sure that's OK
    for count in range(TEST_SIZE):
        count += 1                       # Prevent division by zero in test
        begin_time = utime.ticks_us()
        int_queue.put(count)
        dur = utime.ticks_diff(utime.ticks_us(), begin_time)
        intdursum += dur
        intdurmax = dur if dur > intdurmax else intdurmax

    for count in range(TEST_SIZE):
        count += 1
        begin_time = utime.ticks_us()
        float_queue.put(count)
        dur = utime.ticks_diff(utime.ticks_us(), begin_time)
        floatdursum += dur
        floatdurmax = dur if dur > floatdurmax else floatdurmax

    # Put characters into the byte queue, either one character at a time or by
    # making a string and dumping that into the queue. It seems putting known
    # characters in the queue is very fast; construting f-strings, not so much
    for count in range (BYTE_T_SIZE):
        a_chr = chr(ord('!') + count)
        count += 1
        begin_time = utime.ticks_us()
#         byte_queue.put (a_chr)                # A single character at a time
#         byte_queue.put ('Floofala')             # Several characters at once
        byte_queue.put (f"{a_chr}")           # An f-string of characters
        dur = utime.ticks_diff(utime.ticks_us(), begin_time)
        bytedursum += dur
        bytedurmax = dur if dur > bytedurmax else bytedurmax

    while int_queue.any() and float_queue.any():
        got_this = int_queue.get()
        got_that = float_queue.get()
        if (float(got_this) - got_that) / got_that > 0.0001:
            print (f"Error: got_this != got_that")

    print(f"for {TEST_SIZE} calls to put() in {NUM_QUEUE_SIZE} size queues:")
    print(f"Ints:    Avg {intdursum / TEST_SIZE:.1f}, Max {intdurmax} us")
    print(f"Floats:  Avg {floatdursum / TEST_SIZE:.1f}, Max {floatdurmax} us")
    print(f"Strings: Avg {bytedursum / BYTE_T_SIZE:.1f}, Max {bytedurmax} us")

    # Print just the last 50 characters, or however many are available, from
    # the byte queue. This has been used to verify that the contents are OK
    count = 0
    while byte_queue.any():
        got_char = byte_queue.get()
        if count < 50:
            print(got_char.decode(), end='')
            count += 1
    print('')

    overall["Int Sum"] += intdursum
    overall["Int Max"] = max(overall["Int Max"], intdurmax)
    overall["Float Sum"] += floatdursum
    overall["Float Max"] = max(overall["Float Max"], floatdurmax)
    overall["Byte Sum"] += bytedursum
    overall["Byte Max"] = max(overall["Byte Max"], bytedurmax)


# Run the test suite the given numer of times for a crude reliability test. A
# memory allocation bug has been found in the past by creating and using queues
# many times
for run in range (NUM_RUNS):
    print("")
    print(f"Run {run + 1} of {NUM_RUNS}", end=' ')
    main()

print("")
print(f"Overall results from {NUM_RUNS} runs:")
print(f"Ints:    Avg {overall["Int Sum"] / (TEST_SIZE * NUM_RUNS):.1f}, " +
      f"Max {overall["Int Max"]} us")
print(f"Floats:  Avg {overall["Float Sum"] / (TEST_SIZE * NUM_RUNS):.1f}, " +
      f"Max {overall["Float Max"]} us")
print(f"Strings: Avg {overall["Byte Sum"] / (BYTE_T_SIZE * NUM_RUNS):.1f}, " +
      f"Max {overall["Byte Max"]} us")
print("")

# Check that if invalid data is sent to the queue, an exception is thrown
# rather than having a crash and reboot. It seems particularly evil to try
# to put a queue object into itself
print("The following should throw some TypeErrors:")
booq = cqueue.ByteQueue(10)
for attempt in (1.234, [0, 1, 2], {'one' : 1}, main, "Hel", b"lo!"):
    try:
        booq.put(attempt)
    except TypeError as ohnoes:
        print(f"    Error \"{ohnoes}\" due to put({attempt})")

print(booq)

print("Test finished.")

