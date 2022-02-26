/** @file cqueues.c
 *  This file contains classes which implement queues in C that are linked to
 *  MicroPython. These queues allow data to be transferred between tasks, 
 *  especially interrupt driven tasks, more quickly than it can be using queues
 *  which have been written in Python.
 * 
 *  @author JR Ridgely
 *  @date   2022-Feb-20 JRR Original file, based on some excellent examples 
 *          from the micropython-usermod project, 
 *          @c https://github.com/v923z/micropython-usermod
 *          as well as code in MicroPython's objarray.c.
 *
 *  @copyright (c) 2019-2020 Zoltán Vörös
 *  @copyright (c) 2022 by JR Ridgely, released under the MIT License (MIT)
 *              under terms matching those of the micropython-usermod project.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include <stdio.h>
#include <string.h>
#include "py/runtime.h"
#include "py/obj.h"
#include "py/objstr.h"


/** This structure holds the data of the IntQueue class.
 */
typedef struct _cqueue_IntQueue_obj_t 
{
    mp_obj_base_t base;
    size_t size;                   // Size of the array
    size_t write_idx;              // Array index of write pointer
    size_t read_idx;               // Array index of read pointer
    int32_t* p_data;               // Pointer to array of data
    size_t num_items;              // Number of items currently in the queue
    size_t max_full;               // Maximum number of items in the queue
} cqueue_IntQueue_obj_t;


const mp_obj_type_t cqueue_IntQueue_type;


/** A way to print an IntQueue object; it's used for debugging.
 */
STATIC void IntQueue_print(const mp_print_t *print, 
                           mp_obj_t self_in, 
                           mp_print_kind_t kind) 
{
    (void)kind;
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_print_str(print, "IntQueue[");
    mp_obj_print_helper(print, mp_obj_new_int(self->size), PRINT_REPR);
    mp_print_str(print, "]:");
    for (size_t index = 0; index < self->size; index++)
    {
        mp_obj_print_helper(print, mp_obj_new_int(self->p_data[index]), 
                            PRINT_REPR);
        mp_print_str(print, ",");
    }
    mp_print_str(print, "W:");
    mp_obj_print_helper(print, mp_obj_new_int(self->write_idx), PRINT_REPR);
    mp_print_str(print, ",R:");
    mp_obj_print_helper(print, mp_obj_new_int(self->read_idx), PRINT_REPR);
}


// This forward reference is used a few lines down...
STATIC mp_obj_t IntQueue_clear(mp_obj_t self_in);


/** Create a new queue, allocating memory in which to store the data.
 *  Preallocating the memory is important when we need to pass information from
 *  an interrupt callback, as interrupt code isn't allowed to allocate memory.
 */
STATIC mp_obj_t IntQueue_make_new(const mp_obj_type_t *type,
                                  size_t n_args,
                                  size_t n_kw,
                                  const mp_obj_t *args)
{
    mp_arg_check_num(n_args, n_kw, 1, 1, true);
    cqueue_IntQueue_obj_t *self = m_new_obj(cqueue_IntQueue_obj_t);
    self->base.type = &cqueue_IntQueue_type;
    self->size = mp_obj_get_int(args[0]);

    IntQueue_clear (self);

    // Tried using malloc(); it usually works but occasionally crashes an ESP32
    // apparently when the memory is accessed some time after allocation.
    // After that, tried using n_new() as in objarray.c's array_new()
    // self->p_data = malloc (self->size * sizeof (int32_t));
    self->p_data = (int32_t*)(m_new(byte, sizeof(int32_t) * self->size));

    return MP_OBJ_FROM_PTR(self);
}


/** Set internal variables to indicate an empty queue.
 */
STATIC mp_obj_t IntQueue_clear(mp_obj_t self_in) 
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    self->write_idx = 0;
    self->read_idx = 0;
    self->num_items = 0;
    self->max_full = 0;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_clear_obj, IntQueue_clear);


/** Return @c True if there are any items in the queue, @c False if it's empty.
 */
STATIC mp_obj_t IntQueue_any(mp_obj_t self_in) 
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items > 0);
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_any_obj, IntQueue_any);


/** Return @c True if the queue is full or @c False if there's still room for 
 *  more items.
 */
STATIC mp_obj_t IntQueue_full(mp_obj_t self_in) 
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items >= self->size);
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_full_obj, IntQueue_full);


/** Put an item into the queue. Overwrite old data if the queue is full.
 *  @param to_put An integer to be put into the queue
 */
STATIC mp_obj_t IntQueue_put(mp_obj_t self_in, mp_obj_t to_put)
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);
    int32_t putted = mp_obj_get_int(to_put);

    self->p_data[self->write_idx] = putted;
    self->write_idx++;
    if (self->write_idx >= self->size)
    {
        self->write_idx = 0;
    }

    // If the queue is full before writing, move the read pointer so we'll read
    // old data, not new data
    if (self->num_items >= self->size)
    {
        self->read_idx++;
        if (self->read_idx >= self->size)
        {
            self->read_idx = 0;
        }
    }

    // Now increase the fillage and check again if the queue is full
    self->num_items++;
    if (self->num_items >= self->size)
    {
        self->num_items = self->size;
    }
    if (self->num_items > self->max_full)
    {
        self->max_full = self->num_items;
    }

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(IntQueue_put_obj, IntQueue_put);


/** Get an item from the queue. 
 *  @returns The oldest data in the queue, or @c None if the queue is empty.
 */
STATIC mp_obj_t IntQueue_get(mp_obj_t self_in)
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // Make sure there's something to get
    if (self->num_items == 0)
    {
        return mp_const_none;
    }

    int32_t to_return = self->p_data[self->read_idx];

    // If we get here, the queue has some data in it
    self->read_idx++;
    if (self->read_idx >= self->size)
    {
        self->read_idx = 0;
    }

    self->num_items--;
    if ((int32_t)(self->num_items) <= 0)
    {
        self->num_items = 0;
    }
    return mp_obj_new_int(to_return);
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_get_obj, IntQueue_get);


/** Return the number of items in the queue.
 *  @return The number of items available to be read from the queue
 */
STATIC mp_obj_t IntQueue_available(mp_obj_t self_in) 
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->num_items);
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_available_obj, IntQueue_available);


/** Return the maximum number of items which have been in the queue since the
 *  queue was created or cleared.
 *  @returns The maximum number of items which have been in the queue
 */
STATIC mp_obj_t IntQueue_max_full(mp_obj_t self_in) 
{
    cqueue_IntQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->max_full);
}
MP_DEFINE_CONST_FUN_OBJ_1(IntQueue_max_full_obj, IntQueue_max_full);


/** A dictionary of names and functions used to register the above functions
 *  with MicroPython
 */
STATIC const mp_rom_map_elem_t IntQueue_locals_dict_table[] = 
{
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&IntQueue_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&IntQueue_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_full), MP_ROM_PTR(&IntQueue_full_obj) },
    { MP_ROM_QSTR(MP_QSTR_put), MP_ROM_PTR(&IntQueue_put_obj) },
    { MP_ROM_QSTR(MP_QSTR_get), MP_ROM_PTR(&IntQueue_get_obj) },
    { MP_ROM_QSTR(MP_QSTR_available), MP_ROM_PTR(&IntQueue_available_obj) },
    { MP_ROM_QSTR(MP_QSTR_max_full), MP_ROM_PTR(&IntQueue_max_full_obj) },
};
STATIC MP_DEFINE_CONST_DICT(IntQueue_locals_dict, IntQueue_locals_dict_table);


/** A type which contains the components of the @c cqueue.IntQueue class in 
 *  MicroPython.
 */
const mp_obj_type_t cqueue_IntQueue_type = {
    { &mp_type_type },
    .name = MP_QSTR_IntQueue,
    .print = IntQueue_print,
    .make_new = IntQueue_make_new,
    .locals_dict = (mp_obj_dict_t*)&IntQueue_locals_dict,
};


//=============================================================================


/** This structure holds the data of the FloatQueue class.
 */
typedef struct _cqueue_FloatQueue_obj_t 
{
    mp_obj_base_t base;
    size_t size;                   // Size of the array
    size_t write_idx;              // Array index of write pointer
    size_t read_idx;               // Array index of read pointer
    float* p_data;                 // Pointer to array of data
    size_t num_items;              // Number of items currently in the queue
    size_t max_full;               // Maximum number of items in the queue
} cqueue_FloatQueue_obj_t;


const mp_obj_type_t cqueue_FloatQueue_type;


/** A way to print a FloatQueue object; it's used for debugging.
 */
STATIC void FloatQueue_print(const mp_print_t *print, 
                             mp_obj_t self_in, 
                             mp_print_kind_t kind) 
{
    (void)kind;
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_print_str(print, "FloatQueue[");
    mp_obj_print_helper(print, mp_obj_new_int(self->size), PRINT_REPR);
    mp_print_str(print, "]:");
    for (size_t index = 0; index < self->size; index++)
    {
        mp_obj_print_helper(print, mp_obj_new_float(self->p_data[index]), 
                            PRINT_REPR);
        mp_print_str(print, ",");
    }
    mp_print_str(print, "W:");
    mp_obj_print_helper(print, mp_obj_new_int(self->write_idx), PRINT_REPR);
    mp_print_str(print, ",R:");
    mp_obj_print_helper(print, mp_obj_new_int(self->read_idx), PRINT_REPR);
}


// This forward reference is used a few lines down...
STATIC mp_obj_t FloatQueue_clear(mp_obj_t self_in);


/** Create a new queue, allocating memory in which to store the data.
 *  Preallocating the memory is important when we need to pass information from
 *  an interrupt callback, as interrupt code isn't allowed to allocate memory.
 */
STATIC mp_obj_t FloatQueue_make_new(const mp_obj_type_t *type, 
                                    size_t n_args, 
                                    size_t n_kw, 
                                    const mp_obj_t *args) 
{
    mp_arg_check_num(n_args, n_kw, 1, 1, true);
    cqueue_FloatQueue_obj_t *self = m_new_obj(cqueue_FloatQueue_obj_t);
    self->base.type = &cqueue_FloatQueue_type;

    self->size = mp_obj_get_int(args[0]);

    FloatQueue_clear (self);

    self->p_data = (float*)(m_new(byte, sizeof(float) * self->size));

    return MP_OBJ_FROM_PTR(self);
}


/** Set internal variables to indicate an empty queue.
 */
STATIC mp_obj_t FloatQueue_clear(mp_obj_t self_in) 
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    self->write_idx = 0;
    self->read_idx = 0;
    self->num_items = 0;
    self->max_full = 0;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_clear_obj, FloatQueue_clear);


// Return True if there are any items in the queue, False if it's empty
STATIC mp_obj_t FloatQueue_any(mp_obj_t self_in) 
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items > 0);
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_any_obj, FloatQueue_any);


/** Return @c True if the queue is full or @c False if there's still room for 
 *  more items without overwriting old ones.
 *  @returns The Python constant @c True if the queue is full or @c False if not
 */
STATIC mp_obj_t FloatQueue_full(mp_obj_t self_in) 
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items >= self->size);
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_full_obj, FloatQueue_full);


/** Put an item into the queue. Overwrite old data if queue is full. 
 *  @param to_put The floating point number to be put into the queue
 */
STATIC mp_obj_t FloatQueue_put(mp_obj_t self_in, mp_obj_t to_put)
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);
    float putted = mp_obj_get_float(to_put);

    self->p_data[self->write_idx] = putted;
    self->write_idx++;
    if (self->write_idx >= self->size)
    {
        self->write_idx = 0;
    }

    // If the queue is full before writing, move the read pointer so we'll read
    // old data, not new data
    if (self->num_items >= self->size)
    {
        self->read_idx++;
        if (self->read_idx >= self->size)
        {
            self->read_idx = 0;
        }
    }

    // Now increase the fillage and check again if the queue is full
    self->num_items++;
    if (self->num_items >= self->size)
    {
        self->num_items = self->size;
    }
    if (self->num_items > self->max_full)
    {
        self->max_full = self->num_items;
    }

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(FloatQueue_put_obj, FloatQueue_put);


/** Get an item from the queue; return @c None if the queue is empty.
 *  @returns The oldest data in the queue, or @c None if none is present
 */
STATIC mp_obj_t FloatQueue_get(mp_obj_t self_in)
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // Make sure there's something to get
    if (self->num_items == 0)
    {
        return mp_const_none;
    }

    float to_return = self->p_data[self->read_idx];

    // If we get here, the queue has some data in it
    self->read_idx++;
    if (self->read_idx >= self->size)
    {
        self->read_idx = 0;
    }

    self->num_items--;
    if ((int32_t)(self->num_items) <= 0)
    {
        self->num_items = 0;
    }
    return mp_obj_new_float(to_return);
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_get_obj, FloatQueue_get);


/** Return the number of items in the queue.
 *  @return The number if items available to be read from the queue
 */
STATIC mp_obj_t FloatQueue_available(mp_obj_t self_in) 
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->num_items);
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_available_obj, FloatQueue_available);


/** Return the maximum number of items which have been in the queue since it
 *  was created or last cleared. 
 *  @returns The largest number of items in the queue
 */
STATIC mp_obj_t FloatQueue_max_full(mp_obj_t self_in) 
{
    cqueue_FloatQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->max_full);
}
MP_DEFINE_CONST_FUN_OBJ_1(FloatQueue_max_full_obj, FloatQueue_max_full);


/** A dictionary of names and functions which is used to register functions so
 *  they can be called from MicroPython.
 */
STATIC const mp_rom_map_elem_t FloatQueue_locals_dict_table[] = 
{
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&FloatQueue_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&FloatQueue_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_full), MP_ROM_PTR(&FloatQueue_full_obj) },
    { MP_ROM_QSTR(MP_QSTR_put), MP_ROM_PTR(&FloatQueue_put_obj) },
    { MP_ROM_QSTR(MP_QSTR_get), MP_ROM_PTR(&FloatQueue_get_obj) },
    { MP_ROM_QSTR(MP_QSTR_available), MP_ROM_PTR(&FloatQueue_available_obj) },
    { MP_ROM_QSTR(MP_QSTR_max_full), MP_ROM_PTR(&FloatQueue_max_full_obj) },
};
STATIC MP_DEFINE_CONST_DICT(FloatQueue_locals_dict, 
                            FloatQueue_locals_dict_table);


/** A type which contains the components of the @c cqueue.FloatQueue class in 
 *  MicroPython.
 */
const mp_obj_type_t cqueue_FloatQueue_type = {
    { &mp_type_type },
    .name = MP_QSTR_FloatQueue,
    .print = FloatQueue_print,
    .make_new = FloatQueue_make_new,
    .locals_dict = (mp_obj_dict_t*)&FloatQueue_locals_dict,
};


//=============================================================================


/** This structure holds the data of the ByteQueue class.
 */
typedef struct _cqueue_ByteQueue_obj_t 
{
    mp_obj_base_t base;
    size_t size;                   // Size of the array
    size_t write_idx;              // Array index of write pointer
    size_t read_idx;               // Array index of read pointer
    byte* p_data;                  // Pointer to array of data
    size_t num_items;              // Number of items currently in the queue
    size_t max_full;               // Maximum number of items in the queue
} cqueue_ByteQueue_obj_t;


const mp_obj_type_t cqueue_ByteQueue_type;


/** A way to print a ByteQueue object; it's used for debugging.
 */
STATIC void ByteQueue_print(const mp_print_t *print, 
                             mp_obj_t self_in, 
                             mp_print_kind_t kind) 
{
    (void)kind;
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_print_str(print, "ByteQueue[");
    mp_obj_print_helper(print, mp_obj_new_int(self->size), PRINT_REPR);
    mp_print_str(print, "]:b'");
    for (size_t index = 0; index < self->size; index++)
    {
        // Print characters in approximately Python string printing style
        if (self->p_data[index] > 31 && self->p_data[index] < 127)
        {
            mp_printf(print, "%c", self->p_data[index]);
        }
        else
        {
            mp_printf(print, "\\x%02x", self->p_data[index]);
        }
    }
    mp_print_str(print, "' W:");
    mp_obj_print_helper(print, mp_obj_new_int(self->write_idx), PRINT_REPR);
    mp_print_str(print, ", R:");
    mp_obj_print_helper(print, mp_obj_new_int(self->read_idx), PRINT_REPR);
}


// This forward reference is used a few lines down...
STATIC mp_obj_t ByteQueue_clear(mp_obj_t self_in);


/** Create a new queue, allocating memory in which to store the data.
 *  Preallocating the memory is important when we need to pass information from
 *  an interrupt callback, as interrupt code isn't allowed to allocate memory.
 */
STATIC mp_obj_t ByteQueue_make_new(const mp_obj_type_t *type, 
                                   size_t n_args, 
                                   size_t n_kw, 
                                   const mp_obj_t *args) 
{
    mp_arg_check_num(n_args, n_kw, 1, 1, true);
    cqueue_ByteQueue_obj_t *self = m_new_obj(cqueue_ByteQueue_obj_t);
    self->base.type = &cqueue_ByteQueue_type;

    self->size = mp_obj_get_int(args[0]);

    ByteQueue_clear (self);

    self->p_data = (byte*)(m_new(byte, sizeof(byte) * self->size));

    return MP_OBJ_FROM_PTR(self);
}


/** Set internal variables to indicate an empty queue.
 */
STATIC mp_obj_t ByteQueue_clear(mp_obj_t self_in) 
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    self->write_idx = 0;
    self->read_idx = 0;
    self->num_items = 0;
    self->max_full = 0;

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_clear_obj, ByteQueue_clear);


/** Return True if there are any items in the queue, False if it's empty
 */
STATIC mp_obj_t ByteQueue_any(mp_obj_t self_in) 
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items > 0);
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_any_obj, ByteQueue_any);


/** Return @c True if the queue is full or @c False if there's still room for 
 *  more items without overwriting old ones.
 *  @returns The Python constant @c True if the queue is full or @c False if not
 */
STATIC mp_obj_t ByteQueue_full(mp_obj_t self_in) 
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_bool (self->num_items >= self->size);
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_full_obj, ByteQueue_full);


/** Put characters into the queue. Overwrite old data if queue is full. 
 *  @param str_obj_in The characters to be put into the queue
 */
STATIC mp_obj_t ByteQueue_put(mp_obj_t self_in, mp_obj_t str_obj_in)
{
    // Ensure that the input is a valid type (prevents crashes)
    if (!mp_obj_is_str_or_bytes(str_obj_in))
    {
        mp_raise_TypeError("Bytes or string required");
    }

    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // Get the length of the bytearray or string and a data pointer
    GET_STR_DATA_LEN(str_obj_in, my_str, str_len);

    // Copy the data into the queue, overwriting old data if it's there
    for (size_t index = 0; index < str_len; index++)
    {
        self->p_data[self->write_idx] = my_str[index];
        self->write_idx++;
        if (self->write_idx >= self->size)
        {
            self->write_idx = 0;
        }
        if (self->num_items >= self->size)     // If the queue is full before 
        {                                      // writing, move read pointer
            self->read_idx++;                  // so we'll read old data,
            if (self->read_idx >= self->size)  // not new data
            {
                self->read_idx = 0;
            }
        }
        self->num_items++;                     // Now increase the fillage and
        if (self->num_items >= self->size)     // check again if the queue is
        {                                      // full
            self->num_items = self->size;
        }
        if (self->num_items > self->max_full)
        {
            self->max_full = self->num_items;
        }
    }

    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(ByteQueue_put_obj, ByteQueue_put);


/** Get an item from the queue; return @c None if the queue is empty.
 *  @returns The oldest data in the queue, or @c None if none is present
 */
STATIC mp_obj_t ByteQueue_get(mp_obj_t self_in)
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    // Make sure there's something to get
    if (self->num_items == 0)
    {
        return mp_const_none;
    }

    byte to_return = self->p_data[self->read_idx];

    // If we get here, the queue has some data in it
    self->read_idx++;
    if (self->read_idx >= self->size)
    {
        self->read_idx = 0;
    }

    self->num_items--;
    if ((int32_t)(self->num_items) <= 0)
    {
        self->num_items = 0;
    }
    return mp_obj_new_bytes(&to_return, 1);
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_get_obj, ByteQueue_get);


/** Return the number of items in the queue.
 *  @return The number if items available to be read from the queue
 */
STATIC mp_obj_t ByteQueue_available(mp_obj_t self_in) 
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->num_items);
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_available_obj, ByteQueue_available);


/** Return the maximum number of items which have been in the queue since it
 *  was created or last cleared. 
 *  @returns The largest number of items in the queue
 */
STATIC mp_obj_t ByteQueue_max_full(mp_obj_t self_in) 
{
    cqueue_ByteQueue_obj_t *self = MP_OBJ_TO_PTR(self_in);

    return mp_obj_new_int (self->max_full);
}
MP_DEFINE_CONST_FUN_OBJ_1(ByteQueue_max_full_obj, ByteQueue_max_full);


/** A dictionary of names and functions which is used to register functions so
 *  they can be called from MicroPython.
 */
STATIC const mp_rom_map_elem_t ByteQueue_locals_dict_table[] = 
{
    { MP_ROM_QSTR(MP_QSTR_clear), MP_ROM_PTR(&ByteQueue_clear_obj) },
    { MP_ROM_QSTR(MP_QSTR_any), MP_ROM_PTR(&ByteQueue_any_obj) },
    { MP_ROM_QSTR(MP_QSTR_full), MP_ROM_PTR(&ByteQueue_full_obj) },
    { MP_ROM_QSTR(MP_QSTR_put), MP_ROM_PTR(&ByteQueue_put_obj) },
    { MP_ROM_QSTR(MP_QSTR_get), MP_ROM_PTR(&ByteQueue_get_obj) },
    { MP_ROM_QSTR(MP_QSTR_available), MP_ROM_PTR(&ByteQueue_available_obj) },
    { MP_ROM_QSTR(MP_QSTR_max_full), MP_ROM_PTR(&ByteQueue_max_full_obj) },
};
STATIC MP_DEFINE_CONST_DICT(ByteQueue_locals_dict, 
                            ByteQueue_locals_dict_table);


/** A type which contains the components of the @c cqueue.ByteQueue class in 
 *  MicroPython.
 */
const mp_obj_type_t cqueue_ByteQueue_type = {
    { &mp_type_type },
    .name = MP_QSTR_ByteQueue,
    .print = ByteQueue_print,
    .make_new = ByteQueue_make_new,
    .locals_dict = (mp_obj_dict_t*)&ByteQueue_locals_dict,
};


//=============================================================================


/** This table holds the globals: module name and class(es).
 */
STATIC const mp_map_elem_t cqueue_globals_table[] = 
{
    { MP_OBJ_NEW_QSTR(MP_QSTR___name__), MP_OBJ_NEW_QSTR(MP_QSTR_cqueue) },
    { MP_OBJ_NEW_QSTR(MP_QSTR_IntQueue), (mp_obj_t)&cqueue_IntQueue_type },
    { MP_OBJ_NEW_QSTR(MP_QSTR_FloatQueue), (mp_obj_t)&cqueue_FloatQueue_type },
    { MP_OBJ_NEW_QSTR(MP_QSTR_ByteQueue), (mp_obj_t)&cqueue_ByteQueue_type },
};


STATIC MP_DEFINE_CONST_DICT (
    mp_module_cqueue_globals,
    cqueue_globals_table
);


const mp_obj_module_t cqueue_user_cmodule = 
{
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&mp_module_cqueue_globals,
};


MP_REGISTER_MODULE(MP_QSTR_cqueue, 
                   cqueue_user_cmodule, 
                   1);
