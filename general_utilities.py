#! /usr/bin/env python

"""
Various general programming/math/plotting utilities I wrote - see docstring for each function for what it does.
Weronika Patena, 2010-2011
"""

from __future__ import division 
import sys, os
import subprocess
from collections import defaultdict
import unittest


######################################## STRUCTURES / CLASSES / ETC ########################################

### list/dictionary/etc utilities

def reduce_dicts_to_overlaps(dict_list, exception_on_different_values=False):
    """ Given a list of dictionaries, return a similar new list of dicts with only the keys shared by all the dictionaries.
    Caution: returns a LIST OF DICTS, NOT a new dictionary that contains only the overlap! Easy to get confused."""
    # get the set of keys present in all dictionaries (set intersection)
    if len(dict_list)==0:   return []
    # generate list of keys that are in ALL dictionaries (starting from the list of the first one and reducing)
    overlap_keys = set(dict_list[0].keys())
    for d in dict_list:     overlap_keys &= set(d.keys())
    # make a new dictionary list
    new_dict_list = []
    for d in dict_list:     
        new_reduced_dict = dict([(k,v) for (k,v) in d.iteritems() if k in overlap_keys])
        new_dict_list.append(new_reduced_dict)
    return new_dict_list

def invert_list_to_dict(input_list):
    """ Given a list with no duplicates, return a dict mapping the values to list positions: [a,b,c] -> {a:1,b:2,c:3}."""
    if not len(set(input_list)) == len(input_list):
        raise ValueError("Can't reliably invert a list with duplicate elements!")
    return dict([(value,index) for (index,value) in enumerate(input_list)])

def invert_dict_nodups(input_dict):
    """ Given a dict with no duplicate values, return value:key dict: {a:1,b:2]} -> {1:a,2:b}."""
    if not len(set(input_dict.values())) == len(input_dict.values()):
        raise ValueError("This method can't invert a dictionary with duplicate values! Use invert_dict_tolists.")
    return dict([(value,key) for (key,value) in input_dict.iteritems()])

def invert_dict_tolists(input_dict):
    """ Given a dict (duplicate values allowed), return value:key_list dict: {a:1,b:2,c:1]} -> {1:[a,c],2:b}."""
    inverted_dict = defaultdict(lambda: set())
    for key,value in input_dict.iteritems():
        inverted_dict[value].add(key)
    return dict(inverted_dict)      # changing defaultdict to plain dict to avoid surprises

def invert_listdict_tolists(input_dict):
    """ Given a dict with list/set values, return single_value:key_list dict: {a:[1,2],b:[2]]} -> {1:[a],2:[a,b]}."""
    inverted_dict = defaultdict(lambda: set())
    for key,value_list in input_dict.iteritems():
        try:
            for value in value_list:
                inverted_dict[value].add(key)
        except TypeError:
            raise ValueError("invert_listdict_tolists expects all input_dict values to be lists/sets/etc!")
    return dict(inverted_dict)      # changing defaultdict to plain dict to avoid surprises

class keybased_defaultdict(defaultdict):
    """ A defaultdict equivalent that passes the key as an argument to the default-value factory, instead of no argumnets.
    Normal defaultdict(int)[9] is 0, because no argument is passed to the int function, and int() is 0.  
    On the other hand keybased_defaultdict(int)[9] would be 9, keybased_defaultdict(bool)[9] would be True, etc.  """
    # from http://stackoverflow.com/questions/2912231/is-there-a-clever-way-to-pass-the-key-to-defaultdicts-default-factory
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        else:
            value = self[key] = self.default_factory(key)
            return value

### Useful class mix-ins

class FrozenClass(object):
    """ Class that allows prevention of adding new attributes after creation.
    Use by inheriting from this, and then running self._freeze() at the end of __init__, like this:
        class Test_freezing(FrozenClass):
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self._freeze() # no new attributes after this point.
        a = Test_freezing(2,3)
        a.x = 10    # can modify existing attributes after creation
        a.z = 10    # fails - cannot add NEW atributes after creation
    """
    # by Jochen Ritzel on Stackoverflow 
    #   (http://stackoverflow.com/questions/3603502/prevent-creating-new-attributes-outside-init)
    # This has to be a new-style class (i.e. inheriting from object), old-style classes don't seem to have __setattr__?

    __isfrozen = False

    def __setattr__(self, key, value):
        if self.__isfrozen and not hasattr(self, key):
            raise TypeError( "%r is a frozen class" % self )
        object.__setattr__(self, key, value)
    
    def _freeze(self):
        self.__isfrozen = True

# MAYBE-TODO could/should these be done as a decorators instead?

    
######################################## FILE READING/WRITING, COMMAND-LINE STUFF  ########################################

### Read various file types

# general function for reading input from various sources
from read_input import read_input

def read_two_column_file(filename,numerical_values=True):
    """ Read in a two-column (name,value) tab-separated file (ignore #-comment lines), return data:float(value) dict. """
    data_dict = {}
    for line in open(filename):
        if line[0]=='#':    continue
        name,value = line.strip().split('\t')
        if numerical_values:    data_dict[name] = float(value)
        else:                   data_dict[name] = value
    return data_dict

def read_tab_separated_file(filename, ignore_comments=True):
    """ Read in a tab-separated file (ignore #-comment lines), return a list for each column. """
    for line in open(filename):
        if ignore_comments and line[0]=='#':    continue
        fields = line.strip().split('\t')
        try:
            for i in range(len(fields)): data_list[i].append(fields[i])
        except NameError:
            data_list = [[x] for x in fields]
        if not len(fields)==len(data_list):
            sys.exit("Error: Found line with %s columns, but first line had %s columns! (line %s)"%(len(fields), 
                                                                                                    len(data_list), line))
    return data_list
    # TODO add to unit-tests? Or some kind of test.

def read_tab_separated_file_with_headers(filename, ID_column=0, ignore_comments=True, all_values_are_numbers=False):
    """ Read a tab-separated file with column headers in the first line; ignore comment lines (starting with #) unless specified otherwise. Return a list of IDs from ID_column (in order), and a column_header:column_data dictionary, with one entry per non-ID column, where column_data is an ID:value dictionary with values taken from the column with that header."""
    list_of_column_data = read_tab_separated_file(filename,ignore_comments)
    ID_list = list_of_column_data.pop(ID_column)    # grab the ID column and remove it from data column list
    ID_list.pop(0)                                  # discard header from ID column
    data_dict_by_header = {}
    for column_data in list_of_column_data:
        # grab header, put the rest in a dictionary by ID, in order
        colheader = column_data.pop(0)
        if all_values_are_numbers:
            data_dict_by_header[colheader] = dict([(ID_list[i],float(column_data[i])) for i in range(len(column_data))])
        else:
            data_dict_by_header[colheader] = dict([(ID_list[i],column_data[i]) for i in range(len(column_data))])
    return ID_list, data_dict_by_header
    # TODO add to unit-tests? Or some kind of test.


### Writing to files

# DECORATOR
def replaces_infile_with_outfile(function_to_be_decorated):
    """ DECORATOR, takes a function that takes an infile and outfile and makes it replace infile with outfile instead. 
    The decorated function must still have an argument named outfile, but its value will never be used."""
    def wrapped_function(infile, *args, **kwargs):
        outfile = '.__tmp__'+infile
        kwargs['outfile'] = outfile
        return_val = function_to_be_decorated(infile, *args, **kwargs)
        if os.path.exists(infile):
            os.remove(infile)
        os.rename(outfile,infile)
        return return_val
    return wrapped_function
    # MAYBE-TODO is the way I'm doing this decorator really the best?  Not bad, but requires adding the fake "outfile" argument to all the functions... If I was somehow the function_to_be_decorated's variable list directly instead (with f.__dict__ or f.__setattr__), that wouldn't be an issue... Ask on stackoverflow?
    # TODO add to unit-tests? Or some kind of test.

def save_line_list_as_file(line_list, filename, header="", add_newlines=True):
    """ Given a list of lines, a filename, and an optional header, open file, write header and all lines, close. """
    line_end = "\n" if add_newlines else ""
    # using the with-as syntax automatically closes the file afterward
    with open(filename,'w') as OUTFILE:
        if header:               OUTFILE.write(header+line_end)
        for line in line_list:   OUTFILE.write(line+line_end)

def write_header_data(OUTFILE,options=None):
    """ Print general script run data (command, path, date/time, full optparse options, etc) to given open file object."""
    import sys,os,pwd,time,socket
    OUTFILE.write("# Command line this file was generated with: %s\n"%(' '.join(sys.argv)))
    OUTFILE.write("# Path: %s\n"%(os.getcwd()))
    OUTFILE.write("# Date: %s,\t\tUser: %s,\t\tSystem: %s\n"%(time.ctime(), pwd.getpwuid(os.getuid())[0], 
                                                              socket.gethostname()))
    if options:     OUTFILE.write("# Full options: %s\n"%options)

def print_text_from_file(infile, OUTFILE=None, printing=True, add_newlines=0):
    """ Write all text from infile to OUTFILE (if not None), also print to stdout if printing is set. 
    Return line counts.  Infile should be a filename; OUTFILE should be an open file object. """
    line_count = 0
    for line in open(infile):
        if OUTFILE is not None:     OUTFILE.write(line)
        if printing:                print line,
        line_count += 1
    if add_newlines:
        if OUTFILE is not None:     OUTFILE.write('\n'*add_newlines)
        if printing:                print '\n'*add_newlines,
    return line_count


### Command/line utilities (running processes, getting output, etc)

def run_command_and_print_info(command, LOGFILE=None, printing=True, shell=True, program_name=None):
    """ Run command using subprocess.call; first print a line describing that to LOGFILE and/or stdout.
    The shell arg to subprocess.call is given by shell; LOGFILE should be an open file object; 
    program_name is only used for printing, and the first word of the command will be used by default. """
    if program_name is None:
        program_name = command.split(' ')[0]
    output = "### Running %s: %s"%(program_name, command)
    if LOGFILE is not None:     LOGFILE.write(output+'\n')
    if printing:                print output
    subprocess.call([command], shell=shell)


######################################## NUMERIC DATA MANIPULATION ########################################

### Get rid of nan/inf numbers singly or in lists/dicts, replace by input

def clean_number(val,replace_NaN,replace_Inf,replace_NegInf,make_positive=False):
    """ Replace NaN/Inf/NegInf value with arguments provided, otherwise return input. Also make val positive if asked. """
    from numpy import isnan,isinf,isneginf
    if isnan(val):            return replace_NaN
    elif isinf(val):          return replace_Inf
    elif isneginf(val):       return replace_NegInf
    elif make_positive and val<=0:  return replace_NegInf
    else:                           return val
    # TODO add to unit-tests

def clean_data(input_data,replace_NaN,replace_Inf=None,replace_NegInf=None,make_positive=False):
    """ Take a list/tuple/set/dict, return same with NaN/Inf/negative values replaced with the respective arguments. """
    from numpy import isnan,isinf,isneginf
    # if list/tuple/set, just treat as a list and transform back at the end
    if type(input_data) in (list,tuple,set):
        input_list = list(input_data)
    # if dictionary, take the key and value lists, clean the value list, then transform back to dict at the end
    elif type(input_data)==dict:
        key_list = input_data.keys()
        input_list = [input_data[x] for x in key_list]
    else:
        raise ValueError("input_data argument must be a list, tuple, set or dictionary")
    # if replace_NegInf/replace_Inf weren't set, set them to lower/higher than current min/max value
    if replace_NegInf==None:    
        if make_positive:   replace_NegInf = min([x for x in input_list if x>0 and not isnan(x)])
        else:               replace_NegInf = min([x for x in input_list if not isneginf(x) and not isnan(x)])
        if replace_NegInf<0:    replace_NegInf *=1.5
        else:           replace_NegInf *= 0.5
    if replace_Inf==None:    replace_Inf = 1.5 * max([x for x in input_list if not isinf(x) and not isnan(x)])
    # use clean_number to make a cleaned value list
    new_list = [clean_number(x,replace_NaN,replace_Inf,replace_NegInf,make_positive) for x in input_list]
    # output - switch back to original input type
    if type(input_data)==list:      return new_list
    elif type(input_data)==tuple:   return tuple(new_list)
    elif type(input_data)==set:     return set(new_list)
    elif type(input_data)==dict:    return dict(zip(key_list,new_list))
    # TODO add to unit-tests

def clean_data_remove(input_data,remove_NaN=True,remove_Inf=True,remove_NegInf=True,remove_negative=False,remove_zero=False):
    """ Take a list/tuple/set/dict, return same with NaN/Inf/NegInfo/negative values removed accordint to arguments. """
    from numpy import isnan,isinf,isneginf
    def bad_value(x):
        if remove_NaN and isnan(x):         return True
        elif remove_Inf and isinf(x):       return True
        elif remove_NegInf and isneginf(x): return True
        elif remove_negative and x<0:       return True
        elif remove_zero and x==0:          return True
        return False
    # if list/tuple/set, just treat as a list and transform back at the end
    if type(input_data) in (list,tuple,set):
        new_data = [x for x in input_data if not bad_value(x)]
        if type(input_data)==list:      return new_data
        elif type(input_data)==tuple:   return tuple(new_data)
        elif type(input_data)==set:     return set(new_data)
    # if dictionary, have to use a different removal method
    elif type(input_data)==dict:
        return dict([(k,x) for (k,x) in input_data.iteritems() if not bad_value(x)])
    else:
        raise ValueError("input_data argument must be a list, tuple, set or dictionary")
    # TODO add to unit-tests


### cutoffs, ranges, sets, etc 

def parse_cutoffs_into_ranges(cutoff_list, if_overlapping):
    """ Given a cutoff_list [0,2,5], return [(0,inf),(2,inf),(5,inf)] if if_overlapping, else [(0,2),(2,5),(5,inf)]. """ 
    if not if_overlapping:
        return [(x,float('inf')) for x in cutoff_list]
    ranges = []
    for i in range(len(cutoff_list)-1):
        ranges.append((cutoff_list[i],cutoff_list[i+1]))
    ranges.append((cutoff_list[-1],float('inf')))
    return ranges
    # TODO add to unit-tests

def get_sets_from_cutoffs(value_dict, value_ranges):
    """ Given a (name:val) dictionary and a list of (min,max) value ranges, return a (range:names_in_range) dict. """
    ranges_to_sets = {}
    for (vmin,vmax) in value_ranges:
        ranges_to_sets[(vmin,vmax)] = [name for (name,val) in value_dict.items() if val>=vmin and val<vmax]
    return ranges_to_sets
    # TODO add to unit-tests


### moving average and moving median, plus some help functions (anything starting with _ won't be imported)

def _check_input(data,window_size):
    if window_size<1 or window_size>len(data):   raise ValueError, "window size must be between 1 and data length."

def _make_window_indices(data,window_size):
    half_window = int(window_size/2)
    index_values = [i+half_window for i in range(len(data)-window_size+1)]
    return index_values


def moving_average(data,window_size=10,return_indices=False):
    """ Return the moving average of the input data with the given window size. 

    Optionally also returns the window center indices for plotting. 
    Reasonably efficient implementation, doesn't calculate the whole average for each window.
    """
    _check_input(data,window_size)
    first_average = sum(data[:window_size])/window_size
    average_values = [first_average]
    for i in range(len(data)-window_size):
        # for each new average, just take the previous one, subtract the oldest data value and add the new data value
        new_average = average_values[-1] + (data[i+window_size]-data[i])/window_size
        average_values.append(new_average)
    if return_indices:  return average_values, _make_window_indices(data,window_size)
    else:               return average_values 
    # TODO add to unit-tests


def moving_median(data,window_size=10,return_indices=False):
    """ Return the moving median of the input data with the given window size. 

    Optionally also returns the window center indices for plotting. 
    """
    _check_input(data,window_size)
    from numpy import median
    median_values = []
    for i in range(len(data)-window_size+1):
        median_values.append(median(data[i:i+window_size]))
    if return_indices:  return median_values, _make_window_indices(data,window_size)
    else:               return median_values 
    # TODO add to unit-tests


def plot_function_by_window_size(data,window_size_list,function,figsize=(),title='',xlabel='',xlim=None,ylim=None,yticks=None,ylabel=''):
    """ Return a plot of function on data, with a subplot for each window_size_list value. """
    import matplotlib.pyplot as mplt
    if figsize: fig = mplt.figure(figsize=figsize)
    else:       fig = mplt.figure()
    for i in range(len(window_size_list)):
        window_size = window_size_list[i]
        mplt.subplot(len(window_size_list),1,i+1)
        if i==0 and title:                          mplt.title(title)
        if i==len(window_size_list)-1 and xlabel:   mplt.xlabel(xlabel)
        function_values, indices = function(data, window_size, return_indices=True)
        mplt.plot(indices, function_values, 'b,',linestyle='none') 
        if ylim:    mplt.ylim(ylim[0],ylim[1])
        if xlim:    mplt.xlim(xlim[0],xlim[1])
        if yticks:  mplt.yticks(yticks[0],yticks[1] if len(yticks)>1 else yticks[0])
        if ylabel:  mplt.ylabel(ylabel%window_size)
    return fig
    # TODO how would one even test this?



### Convert data into linlog scale (slightly weird, for plotting) - OLD CODE, STILL IN PROGRESS, will pick it back up if it's needed for anything.
# for example, if cutoff=10, what we want is: 1->1, 2->2, 5->5, 10->10, 100->20, 1000->30, 10000->40, ...
#  if cutoff=100, what we want is: 1->1, 2->2, 5->5, 10->10, 50->50, 100->100, 1000->200, 10000->300, 100000->400, ...
#  if cutoff=1, what we want is: 1->1, 10->2, 100->3, 1000->4, ...
# TODO this should probably just return a graph instead of the values!  Since there's no conceivable use for this except for graphing.  And then I could make the graph have extra features, like ticks/labels and a lin/log transition mark.
### TODO this example shows the proper way of implementing a custom scale in matplotlib: 
# http://matplotlib.sourceforge.net/examples/api/custom_scale_example.html
# also see StackOverflow: http://stackoverflow.com/questions/6382612/python-equivalent-for-matlabs-normplot/6382851#6382851
def convert_data_to_linlog(dataset,cutoff=10):
    """ Convert the data (list of numbers) for correct plotting on a scale that's linear up to cutoff and log afterward."""
    from math import log10
    cutoff=float(cutoff)
    dataset_linlog = []
    for x in dataset:
        if x <= cutoff:
            dataset_linlog.append(x)
        else:
            dataset_linlog.append((log10(x/cutoff)+1)*cutoff)
    return dataset_linlog
# TODO now how to label it correctly?  Basically first make the graph, get the resulting tick values, and run convert_data_to_linlog on them to get the tick labels.
# the fuctions is mplt.yticks([0,1,2,5,10,20,30,40],['0','1','2','5','10','100','1000','10000'])
# TODO maybe put a transition mark where the scale changes from lin to log?



######################################## TESTS FOR THIS FILE ########################################

class Testing_everything(unittest.TestCase):
    """ Testing all functions/classes.etc. """

    def test__reduce_dicts_to_overlaps(self):
        d1 = {1:1}
        d2 = {1:2, 2:2}
        d3 = {2:3, 3:3}
        print reduce_dicts_to_overlaps([d1,d2])
        assert reduce_dicts_to_overlaps([d1,d2]) == [{1:1},{1:2}] 
        assert reduce_dicts_to_overlaps([d2,d3]) == [{2:2},{2:3}] 
        assert reduce_dicts_to_overlaps([d1,d3]) == [{},{}] 
        assert reduce_dicts_to_overlaps([d1,d2,d3]) == [{},{},{}] 
        assert reduce_dicts_to_overlaps([]) == [] 

    def test__invert_list_to_dict(self):
        assert invert_list_to_dict([]) == {}
        assert invert_list_to_dict([10,12,11]) == {10:0, 12:1, 11:2}
        assert invert_list_to_dict(['a',None,11]) == {'a':0, None:1, 11:2}
        self.assertRaises(ValueError, invert_list_to_dict, [10,11,10])
        self.assertRaises(ValueError, invert_list_to_dict, [None,None])

    def test__invert_dict_nodups(self):
        assert invert_dict_nodups({}) == {}
        assert invert_dict_nodups({1:2,3:4}) == {2:1,4:3}
        self.assertRaises(ValueError, invert_dict_nodups, {1:2,3:2})

    def test__invert_dict_tolists(self):
        assert invert_dict_tolists({}) == {}
        assert invert_dict_tolists({1:2,3:4}) == {2:set([1]),4:set([3])}
        assert invert_dict_tolists({1:2,3:2}) == {2:set([1,3])}

    def test__invert_listdict_tolists(self):
        assert invert_listdict_tolists({}) == {}
        assert invert_listdict_tolists({1:[2],3:[4]}) == {2:set([1]),4:set([3])}
        assert invert_listdict_tolists({1:[2],3:[2]}) == {2:set([1,3])}
        assert invert_listdict_tolists({1:[2,4],3:[2]}) == {2:set([1,3]),4:set([1])}
        self.assertRaises(ValueError, invert_dict_nodups, {1:2,3:2})

    def test__keybased_defaultdict(self):
        D_nodefault = keybased_defaultdict(None)
        self.assertRaises(KeyError, lambda: D_nodefault[1])
        D_constantdefault = keybased_defaultdict(lambda x: 0)
        assert D_constantdefault[1] == 0
        assert D_constantdefault[2] == 0
        D_variabledefault = keybased_defaultdict(lambda x: 2*x)
        assert D_variabledefault[1] == 2
        assert D_variabledefault[2] == 4

    def test__FrozenClass(self):
        class Test_freezing(FrozenClass):
            def __init__(self, x, y):
                self.x = x
                self.y = y
                self._freeze() # no new attributes after this point.
        a = Test_freezing(2,3)
        assert a.x == 2
        a.x = 10    # can modify existing attributes after creation - shouldn't raise an exception
        assert a.x == 10
        # doing a.z = 10 should fail - cannot add NEW atributes after creation
        #  testing this two ways: with __setattr__ as a function, and with writing a test function to explicitly 
        #  test the "a.z = 1" statement (which of course should use __setattr__ anyway, but may as well check)
        self.assertRaises(TypeError, a.__setattr__, 'z', 10)
        def test_function(obj,val):  
            obj.z = val
        self.assertRaises(TypeError, test_function, a, 10)

    # TODO add tests for everything else

if __name__=='__main__':
    """ If module is ran directly, run tests. """
    print "This is a module for import by other programs - it doesn't do anything on its own.  Running tests..."
    unittest.main()
