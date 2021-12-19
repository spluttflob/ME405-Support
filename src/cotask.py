"""!
@file cotask.py
This file contains classes to run cooperatively scheduled tasks in a
multitasking system.

Tasks are created as generators, functions which have infinite loops and call
@c yield at least once in the loop. References to all the tasks to be run
in the system are kept in a list maintained by class @c CoTaskList; the 
system scheduler then runs the tasks' @c run() methods according to a 
chosen scheduling algorithm such as round-robin or highest-priority-first. 

@author JR Ridgely
@date   2017-Jan-01 JRR Approximate date of creation of file
@date   2021-Dec-18 JRR Docstrings modified to work without DoxyPyPy
@copyright This program is copyright (c) 2017-2021 by JR Ridgely and released
           under the GNU Public License, version 3.0. 
"""

import gc                              # Memory allocation garbage collector
import utime                           # Micropython version of time library
import micropython                     # This shuts up incorrect warnings


class Task:
    """!
    Implements multitasking with scheduling and some performance logging.

    This class implements behavior common to tasks in a cooperative 
    multitasking system which runs in MicroPython. The ability to be scheduled
    on the basis of time or an external software trigger or interrupt is 
    implemented, state transitions can be recorded, and run times can be
    profiled. The user's task code must be implemented in a generator which
    yields the state (and the CPU) after it has run for a short and bounded 
    period of time. 

    Example:
      @code
          def task1_fun ():
              '''! This function switches states repeatedly for no reason '''
              state = 0
              while True:
                  if state == 0:
                      state = 1
                  elif state == 1:
                      state = 0
                  yield (state)

          # In main routine, create this task and set it to run twice per second
          task1 = cotask.Task (task1_fun, name = 'Task 1', priority = 1, 
                               period = 500, profile = True, trace = True)

          # Add the task to the list (so it will be run) and run scheduler
          cotask.task_list.append (task1)
          while True: 
              cotask.task_list.pri_sched ()
      @endcode
      """


    def __init__ (self, run_fun, name = "NoName", priority = 0, 
                  period = None, profile = False, trace = False):
        """!
        Initialize a task object so it may be run by the scheduler.

        This method initializes a task object, saving copies of constructor
        parameters and preparing an empty dictionary for states.
        
        @param run_fun The function which implements the task's code. It must
               be a generator which yields the current state.
        @param name The name of the task, by default @c NoName. This should
               be overridden with a more descriptive name by the programmer.
        @param priority The priority of the task, a positive integer with
               higher numbers meaning higher priority (default 0)
        @param period The time in milliseconds between runs of the task if it's
               run by a timer or @c None if the task is not run by a timer.
               The time can be given in a @c float or @c int; it will be 
               converted to microseconds for internal use by the scheduler.
        @param profile Set to @c True to enable run-time profiling 
        @param trace Set to @c True to generate a list of transitions between
               states. @b Note: This slows things down and allocates memory.
        """
        # The function which is run to implement this task's code. Since it 
        # is a generator, we "run" it here, which doesn't actually run it but
        # gets it going as a generator which is ready to yield values
        self._run_gen = run_fun ()

        ## The name of the task, hopefully a short and descriptive string.
        self.name = name

        ## The task's priority, an integer with higher numbers meaning higher 
        #  priority. 
        self.priority = int (priority)

        ## The period, in milliseconds, between runs of the task's @c run()
        #  method. If the period is @c None, the @c run() method won't be run
        #  on a time basis but will instead be run by the scheduler as soon
        #  as feasible after code such as an interrupt handler calls the 
        #  @c go() method. 
        if period != None:
            self.period = int (period * 1000)
            self._next_run = utime.ticks_us () + self.period
        else:
            self.period = period
            self._next_run = None

        # Flag which causes the task to be profiled, in which the execution
        #  time of the @c run() method is measured and basic statistics kept. 
        self._prof = profile
        self.reset_profile ()

        # The previous state in which the task last ran. It is used to watch
        # for and track state transitions.
        self._prev_state = 0

        # If transition tracing has been enabled, create an empty list in 
        # which to store transition (time, to-state) stamps
        self._trace = trace
        self._tr_data = []
        self._prev_time = utime.ticks_us ()

        ## Flag which is set true when the task is ready to be run by the
        #  scheduler
        self.go_flag = False


    def schedule (self) -> bool:
        """!
        This method is called by the scheduler; it attempts to run this task.
        If the task is not yet ready to run, this method returns @c False
        immediately; if this task is ready to run, it runs the task's generator
        up to the next @c yield() and then returns @c True.

        @return @c True if the task ran or @c False if it did not
        """
        if self.ready ():

            # Reset the go flag for the next run
            self.go_flag = False

            # If profiling, save the start time
            if self._prof:
                stime = utime.ticks_us ()

            # Run the method belonging to the state which should be run next
            curr_state = next (self._run_gen)

            # If profiling or tracing, save timing data
            if self._prof or self._trace:
                etime = utime.ticks_us ()

            # If profiling, save timing data
            if self._prof:
                self._runs += 1
                runt = utime.ticks_diff (etime, stime)
                if self._runs > 2:
                    self._run_sum += runt
                    if runt > self._slowest:
                        self._slowest = runt

            # If transition logic tracing is on, record a transition; if not,
            # ignore the state. If out of memory, switch tracing off and 
            # run the memory allocation garbage collector
            if self._trace:
                try:
                    if curr_state != self._prev_state:
                        self._tr_data.append (
                            (utime.ticks_diff (etime, self._prev_time),
                             curr_state))
                except MemoryError:
                    self._trace = False
                    gc.collect ()

                self._prev_state = curr_state
                self._prev_time = etime

            return True

        else:
            return False


    @micropython.native
    def ready (self) -> bool:
        """!
        This method checks if the task is ready to run.
        If the task runs on a timer, this method checks what time it is; if not,
        this method checks the flag which indicates that the task is ready to
        go. This method may be overridden in descendent classes to implement
        some other behavior.
        """
        # If this task uses a timer, check if it's time to run run() again. If
        # so, set go flag and set the timer to go off at the next run time
        if self.period != None:
            late = utime.ticks_diff (utime.ticks_us (), self._next_run)
            if late > 0:
                self.go_flag = True
                self._next_run = utime.ticks_diff (self.period, 
                                                   -self._next_run)

                # If keeping a latency profile, record the data
                if self._prof:
                    self._late_sum += late
                    if late > self._latest:
                        self._latest = late

        # If the task doesn't use a timer, we rely on go_flag to signal ready
        return self.go_flag


    def reset_profile (self):
        """!
        This method resets the variables used for execution time profiling.
        This method is also used by @c __init__() to create the variables.
        """
        self._runs = 0
        self._run_sum = 0
        self._slowest = 0
        self._late_sum = 0
        self._latest = 0


    def get_trace (self):
        """!
        This method returns a string containing the task's transition trace.
        The trace is a set of tuples, each of which contains a time and the
        states from and to which the system transitioned. 
        @return A possibly quite large string showing state transitions
        """
        tr_str = 'Task ' + self.name + ':'
        if self._trace:
            tr_str += '\n'
            last_state = 0
            total_time = 0.0
            for item in self._tr_data:
                total_time += item[0] / 1000000.0
                tr_str += '{: 12.6f}: {: 2d} -> {:d}\n'.format (total_time, 
                    last_state, item[1])
                last_state = item[1]
        else:
            tr_str += ' not traced'
        return (tr_str)


    def go (self):
        """!
        Method to set a flag so that this task indicates that it's ready to run.
        This method may be called from an interrupt service routine or from
        another task which has data that this task needs to process soon.
        """
        self.go_flag = True


    def __repr__ (self):
        """!
        This method converts the task to a string for diagnostic use.
        It shows information about the task, including execution time
        profiling results if profiling has been done.
        """
        rst = '{:<16s}{: 4d}'.format (self.name, self.priority)
        try:
            rst += '{: 10.1f}'.format (self.period / 1000.0)
        except TypeError:
            rst += '         -'
        rst += '{: 8d}'.format (self._runs)

        if self._prof and self._runs > 0:
            avg_dur = (self._run_sum / self._runs) / 1000.0
            avg_late = (self._late_sum / self._runs) / 1000.0
            rst += '{: 10.3f}{: 10.3f}'.format (avg_dur, 
                self._slowest / 1000.0)
            if self.period != None:
                rst += '{: 10.3f}{: 10.3f}'.format (avg_late, 
                                            self._latest / 1000.0)
        return rst


# =============================================================================

class TaskList:
    """!
    A list of tasks used internally by the task scheduler.
    This class holds the list of tasks which will be run by the task scheduler.
    The task list is usually not directly used by the programmer except when
    tasks are added to it and the scheduler is called. An example showing the
    use of the task list is given in the last few lines of the documentation
    for class @c Task. 

    The task list is sorted by priority so that the scheduler can efficiently
    look through the list to find the highest priority task which is ready to
    run at any given time. Tasks can also be scheduled in a simpler
    "round-robin" fashion.
    """

    def __init__ (self):
        """!
        Initialize the task list. This creates the list of priorities in
        which tasks will be organized by priority.
        """
        ## The list of priority lists. Each priority for which at least one 
        #  task has been created has a list whose first element is a task 
        #  priority and whose other elements are references to task objects at
        #  that priority. 
        self.pri_list = []


    def append (self, task):
        """!
        Append a task to the task list. The list will be sorted by task 
        priorities so that the scheduler can quickly find the highest priority
        task which is ready to run at any given time. 
        @param task The task to be appended to the list
        """
        # See if there's a tasklist with the given priority in the main list
        new_pri = task.priority
        for pri in self.pri_list:
            # If a tasklist with this priority exists, add this task to it.
            if pri[0] == new_pri:
                pri.append (task)
                break

        # If the priority isn't in the list, this else clause starts a new 
        # priority list with this task as first one. A priority list has the
        # priority as element 0, an index into the list of tasks (used for
        # round-robin scheduling those tasks) as the second item, and tasks
        # after those
        else:
            self.pri_list.append ([new_pri, 2, task])

        # Make sure the main list (of lists at each priority) is sorted
        self.pri_list.sort (key=lambda pri: pri[0], reverse=True)


    @micropython.native
    def rr_sched (self):
        """!
        Run tasks in order, ignoring the tasks' priorities.

        This scheduling method runs tasks in a round-robin fashion. Each
        time it is called, it goes through the list of tasks and gives each of
        them a chance to run. Although this scheduler first runs higher priority
        tasks first, that has no significant effect in the long run, as all the
        tasks are given a chance to run each time through the list, and it takes
        about the same amount of time before each is given a chance to run 
        again.
        """
        # For each priority level, run all tasks at that level
        for pri in self.pri_list:
            for task in pri[2:]:
                task.schedule ()


    @micropython.native
    def pri_sched (self):
        """!
        Run tasks according to their priorities.

        This scheduler runs tasks in a priority based fashion. Each time it is
        called, it finds the highest priority task which is ready to run and
        calls that task's @c run() method.
        """
        # Go down the list of priorities, beginning with the highest
        for pri in self.pri_list:
            # Within each priority list, run tasks in round-robin order
            # Each priority list is [priority, index, task, task, ...] where
            # index is the index of the next task in the list to be run
            tries = 2
            length = len (pri)
            while tries < length:
                ran = pri[pri[1]].schedule ()
                tries += 1
                pri[1] += 1
                if pri[1] >= length:
                    pri[1] = 2
                if ran:
                    return


    def __repr__ (self):
        """!
        Create some diagnostic text showing the tasks in the task list.
        """
        ret_str = 'TASK             PRI    PERIOD    RUNS   AVG DUR   MAX ' \
            'DUR  AVG LATE  MAX LATE\n'
        for pri in self.pri_list:
            for task in pri[2:]:
                ret_str += str (task) + '\n'

        return ret_str


## This is @b the main task list which is created for scheduling when 
#  @c cotask.py is imported into a program. 
task_list = TaskList ()




