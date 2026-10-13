"""Original, authored curriculum. No content from the absent question book."""
from textwrap import dedent


def clean(text):
    return dedent(text).strip() + '\n'


def step(line, caption, values, active=None, labels=None, edges=None):
    return dict(line=line, caption=caption, values=[str(v) for v in values], active=active or [], labels=labels or [], edges=edges or [])


def case(expression, expected, name='Example', stdin=None):
    return dict(name=name, expression=expression, expected=expected, stdin=stdin or [])


LESSONS = []


def add(id, title, objective, explanation, code, output, kind, steps, mistake, exercise_title, statement, starter, tests, hints, solution, solution_explanation, constraints, *, track='python', prerequisites=None):
    earlier = [x for x in LESSONS if x['track'] == track]
    prereqs = prerequisites if prerequisites is not None else ([earlier[-1]['id']] if earlier else [])
    LESSONS.append(dict(id=id, track=track, order=len(earlier) + 1, title=title, summary=objective,
        content=dict(objective=objective, explanation=explanation, example=clean(code), expected_output=output, mistake=mistake,
                     demo=dict(kind=kind, code=clean(code), steps=steps), prerequisites=prereqs, minutes=8 if track == 'python' else 12),
        exercise=dict(id=f'{id}-practice', title=exercise_title, statement=statement, starter=clean(starter), tests=tests, hints=hints,
                      solution=clean(solution), explanation=solution_explanation, constraints=constraints, prerequisites=prereqs,
                      examples=[dict(input=t['expression'] or '\\n'.join(t['stdin']), output=t['expected']) for t in tests[:2]],
                      difficulty='Beginner' if track == 'python' else 'Intermediate')))
    if id == 'loops':
        LESSONS[-1]['content']['extra_examples'] = [{
            'title': 'The same idea with a while loop',
            'explanation': 'When the number of repeats depends on a changing condition, use while. Decrementing remaining guarantees this countdown reaches its stopping condition.',
            'code': 'remaining = 3\nwhile remaining > 0:\n    print(remaining)\n    remaining -= 1\nprint("Go!")\n',
            'expected_output': '3\n2\n1\nGo!\n',
        }]


add('values', 'Values & variables', 'Give values a name. Understand what assignment really does.',
    'A value is a piece of data: 42 is an integer, 3.5 a float, "hello" a string, and True a boolean. A variable is a name bound to an object. Assignment binds a name; it does not universally copy objects. Rebinding score below leaves the earlier integer unchanged. Later, lists will show why shared mutable objects matter.',
    'score = 10\nbonus = 5\nscore = score + bonus\nprint(score)', '15\n', 'bindings',
    [step(1, 'score is bound to the integer 10.', [10], [0], ['score']), step(2, 'bonus is a second binding.', [10, 5], [1], ['score', 'bonus']), step(3, 'Addition creates a result; score is rebound to 15.', [15, 5], [0], ['score', 'bonus'])],
    'Names are case-sensitive: Score and score are different. A quoted "10" is text, not the number 10.',
    'A tiny introduction', 'Create name with the string Ada and age with integer 20. Print exactly Ada is 20 using these variables.',
    'name = ""\nage = 0\n# Print a sentence with name and age', [case('', 'Ada is 20\n', 'Introduction')],
    ['Bind name to "Ada" and age to 20.', 'print can accept several arguments separated by commas.', 'Use print(name, "is", age).'],
    'name = "Ada"\nage = 20\nprint(name, "is", age)', 'print inserts spaces between its arguments and ends with a newline.', ['Use a string for name and an integer for age.'])

add('operators', 'Operators & expressions', 'Combine values and predict the order of evaluation.',
    'An expression produces a value. Python evaluates multiplication before addition; parentheses make a different order explicit. / produces a float, // performs floor division, and % gives the remainder. Comparisons such as >= produce booleans. For negative numbers, // rounds down, not toward zero.',
    'total = 3 + 4 * 2\nprint(total)\nprint((3 + 4) * 2)\nprint(17 // 5, 17 % 5)', '11\n14\n3 2\n', 'array',
    [step(1, 'Multiply 4 by 2 before adding 3.', [3, '+', 8], [2]), step(2, 'The first expression produces 11.', [11], [0]), step(4, '17 divided into groups of 5 gives 3 groups and 2 left over.', [5, 5, 5, 2], [3])],
    '^ means bitwise XOR, not exponentiation. Use ** for powers.', 'Minutes to hours',
    'Set minutes to 135. Print the number of whole hours and leftover minutes on one line, separated by a space.',
    'minutes = 135\n# Print whole hours and remaining minutes', [case('', '2 15\n', '135 minutes')],
    ['There are 60 minutes in an hour.', 'Use // for whole hours and % for the remainder.'],
    'minutes = 135\nprint(minutes // 60, minutes % 60)', 'Floor division counts complete hours; modulo gives the remaining minutes.', ['Do not hard-code the printed answer.'])

add('input-output', 'Input & output', 'Turn text input into a useful result.',
    'print() writes output. input() reads one line and always returns a string. Convert numeric text with int() or float() before arithmetic. In this browser editor, place one response per line in the Input panel before running. The runtime consumes these responses in order.',
    'name = input()\nprint(f"Hello, {name}!")', 'Hello, Ada!\n', 'flow',
    [step(1, 'Input buffer contains the text Ada.', ['Ada'], [0], ['input']), step(1, 'The returned string is bound to name.', ['Ada'], [0], ['name']), step(2, 'An f-string inserts the value into a greeting.', ['Hello, Ada!'], [0], ['output'])],
    'input() + 1 fails because input is text. Convert it first; invalid numeric text raises ValueError.', 'Next birthday',
    'Read an age from input and print the age at the next birthday. Do not add a prompt to the output.',
    'age = input()\n# Convert, add one, and print', [case('', '21\n', 'Age 20', ['20']), case('', '1\n', 'Age zero', ['0']), case('', '100\n', 'Age 99', ['99'])],
    ['The input is a string even if it contains digits.', 'int(age) converts the text to an integer.'],
    'age = int(input())\nprint(age + 1)', 'Conversion happens before integer addition.', ['Input is an integer from 0 to 120.'])

add('conditions', 'Conditions & decisions', 'Choose a path using boolean expressions.',
    'if evaluates a condition. Its indented block runs only when that condition is true. elif checks another condition when previous ones failed. else handles the remaining case. Order matters: put a more specific check before a broader check that would also match it.',
    'temperature = 28\nif temperature >= 25:\n    print("warm")\nelse:\n    print("cool")', 'warm\n', 'branch',
    [step(1, 'The current temperature is 28.', [28], [0]), step(2, '28 >= 25 is True, so follow the warm branch.', ['True', 'warm', 'cool'], [0, 1], [], [[0, 1], [0, 2]]), step(3, 'Only the selected branch prints.', ['warm', 'cool'], [0])],
    '= assigns a value. == compares values. Indentation defines each branch.', 'Ticket price',
    'Read an age. Print free for children under 5, child for ages 5 through 17, and adult for ages 18 and above.',
    'age = int(input())\n# Choose the correct ticket', [case('', 'free\n', 'Under five', ['4']), case('', 'child\n', 'Boundary five', ['5']), case('', 'child\n', 'Seventeen', ['17']), case('', 'adult\n', 'Boundary eighteen', ['18'])],
    ['Start by checking age < 5.', 'Use elif age < 18, followed by else.'],
    'age = int(input())\nif age < 5:\n    print("free")\nelif age < 18:\n    print("child")\nelse:\n    print("adult")', 'Each later branch is considered only after earlier conditions fail.', ['Age is an integer from 0 to 120.'])

add('loops', 'Loops & traversal', 'Repeat work with for, while, range, break, and continue.',
    'for visits items in an iterable. range(start, stop) includes start but excludes stop. while repeats while a condition stays true; make sure something moves it toward termination. continue skips the rest of the current iteration. break exits the innermost loop. In the example, 2 is skipped and reaching 5 stops traversal.',
    'for number in range(1, 7):\n    if number == 2:\n        continue\n    if number == 5:\n        break\n    print(number)', '1\n3\n4\n', 'array',
    [step(6, 'Visit 1 and print it.', [1, 2, 3, 4, 5, 6], [0]), step(3, 'continue skips printing 2.', [1, 2, 3, 4, 5, 6], [1]), step(6, 'Print 3, then 4.', [1, 2, 3, 4, 5, 6], [2, 3]), step(5, 'break stops at 5; 6 is never visited.', [1, 2, 3, 4, 5, 6], [4])],
    'A while loop with an unchanged condition can run forever. Use Stop to terminate browser execution.', 'Sum the even numbers',
    'Read n and print the sum of even integers from 0 through n, inclusive. Use a loop.',
    'n = int(input())\ntotal = 0\n# Accumulate even numbers\nprint(total)', [case('', '0\n', 'Zero', ['0']), case('', '6\n', 'Four', ['4']), case('', '12\n', 'Seven', ['7'])],
    ['range(n + 1) includes n.', 'Add a number only when number % 2 == 0.'],
    'n = int(input())\ntotal = 0\nfor number in range(n + 1):\n    if number % 2 == 0:\n        total += number\nprint(total)', 'The accumulator starts at zero and changes only for even values.', ['0 <= n <= 1000.'])

add('functions', 'Functions & return values', 'Package a calculation behind a clear interface.',
    'def creates a function. Parameters name its inputs; arguments are the actual values passed by the caller. return sends a result back and ends the current call. A function without return produces None. Local names belong to the call, while mutable argument objects can still be shared with the caller.',
    'def double(number):\n    return number * 2\n\nresult = double(4)\nprint(result)', '8\n', 'flow',
    [step(4, 'Pass the argument 4 into double.', [4, 'double', '?'], [0], ['argument', 'function', 'return'], [[0, 1], [1, 2]]), step(2, 'The local parameter number refers to 4.', [4, '× 2', 8], [1]), step(5, 'Return 8 to the caller and print it.', [4, 'double', 8], [2])],
    'Printing inside a function is not the same as returning a value.', 'Rectangle area',
    'Implement area(width, height) and return the rectangle area. Do not print inside the function.',
    'def area(width, height):\n    pass', [case('area(3, 4)', 12, 'Rectangle'), case('area(0, 9)', 0, 'Zero width'), case('area(2.5, 4)', 10.0, 'Fractional width')],
    ['Area is width multiplied by height.', 'Use return rather than print.'],
    'def area(width, height):\n    return width * height', 'The return value can be reused by the caller without parsing output.', ['Dimensions are non-negative numbers.'])

add('strings', 'Strings & text', 'Index, slice, and transform immutable text.',
    'A string is an immutable sequence of characters. Indexing starts at zero; negative indices count from the end. A slice s[start:stop] excludes stop. Methods such as strip() and lower() return new strings. They do not modify the original. Use == to compare the contents of strings.',
    'word = "Python"\nprint(word[0])\nprint(word[1:4])\nprint(word.lower())', 'P\nyth\npython\n', 'array',
    [step(2, 'Index zero selects P.', list('Python'), [0]), step(3, 'Slice 1:4 selects indices 1, 2, and 3.', list('Python'), [1, 2, 3]), step(4, 'lower returns a new string.', list('python'), [0])],
    'word[0] = "p" raises TypeError because strings are immutable.', 'Normalize a label',
    'Implement normalize(text): remove leading/trailing whitespace and convert letters to lowercase. Keep internal spaces.',
    'def normalize(text):\n    pass', [case('normalize("  PyTHON  ")', 'python', 'Mixed case'), case('normalize(" A B ")', 'a b', 'Internal space'), case('normalize("   ")', '', 'Whitespace only')],
    ['strip() handles outer whitespace.', 'Chain strip() and lower(), returning the result.'],
    'def normalize(text):\n    return text.strip().lower()', 'Both methods return new strings; chaining applies lower to the stripped result.', ['Input is a string with at most 200 characters.'])

add('lists-tuples', 'Lists, tuples & shared objects', 'Use indexed collections and recognize aliasing.',
    'Lists are mutable, ordered collections. append changes a list in place; indexing retrieves an element. Tuples are ordered but immutable. When two names refer to the same list, a mutation through either name is visible through both. list.copy() makes a shallow copy: nested objects may still be shared.',
    'items = [2, 4]\nalias = items\nalias.append(6)\nprint(items)\npoint = (3, 5)\nprint(point[0])', '[2, 4, 6]\n3\n', 'alias',
    [step(1, 'items is bound to one list object.', ['items', '[2, 4]'], [1], [], [[0, 1]]), step(2, 'alias points to the same object, not a copy.', ['items', '[2, 4]', 'alias'], [2], [], [[0, 1], [2, 1]]), step(3, 'Mutating through alias changes the single shared list.', ['items', '[2, 4, 6]', 'alias'], [1], [], [[0, 1], [2, 1]])],
    'append returns None. Writing items = items.append(6) loses the list binding.', 'Append without changing the original',
    'Implement with_extra(items, value). Return a new list containing items followed by value; leave the original list unchanged.',
    'def with_extra(items, value):\n    pass', [case('with_extra([1, 2], 3)', [1, 2, 3], 'Append'), case('with_extra([], 5)', [5], 'Empty'), case('(lambda a: [with_extra(a, 9), a])([1])', [[1, 9], [1]], 'Original unchanged')],
    ['Make a shallow copy before appending.', 'Use result = items.copy(), then result.append(value).'],
    'def with_extra(items, value):\n    result = items.copy()\n    result.append(value)\n    return result', 'A separate outer list avoids mutating the caller\'s list.', ['items has at most 100 integers; value is an integer.'])

add('dictionaries-sets', 'Dictionaries & sets', 'Look up values by key and remove duplicates.',
    'A dictionary maps unique, hashable keys to values. Access a required key with d[key]; use d.get(key, default) when it might be absent. A set stores unique hashable elements and supports fast membership checks. Set iteration order is not a sorting guarantee; sort when output order matters.',
    'scores = {"Ada": 8, "Lin": 6}\nscores["Ada"] += 1\nprint(scores["Ada"])\nprint(sorted(set([3, 1, 3])))', '9\n[1, 3]\n', 'mapping',
    [step(1, 'Each key maps to one value.', ['Ada → 8', 'Lin → 6'], [0]), step(2, 'Update the value stored for Ada.', ['Ada → 9', 'Lin → 6'], [0]), step(4, 'A set removes repeated 3; sorting makes order explicit.', [1, 3], [0, 1])],
    'A missing d[key] raises KeyError. An empty {} is a dictionary, not a set.', 'Count words',
    'Implement counts(words), returning a dictionary from each word to its frequency. Matching is case-sensitive.',
    'def counts(words):\n    pass', [case('counts(["a", "b", "a"])', {'a': 2, 'b': 1}, 'Repeated word'), case('counts([])', {}, 'Empty'), case('counts(["A", "a"])', {'A': 1, 'a': 1}, 'Case sensitive')],
    ['Start with an empty dictionary and iterate over words.', 'Use result.get(word, 0) + 1 for each update.'],
    'def counts(words):\n    result = {}\n    for word in words:\n        result[word] = result.get(word, 0) + 1\n    return result', 'get supplies zero before the first occurrence of a word.', ['At most 100 words; every word is a string.'])

add('exceptions', 'Exceptions & recovery', 'Handle an expected failure without hiding other bugs.',
    'Exceptions interrupt ordinary execution. Put a risky operation in try and catch the specific exception you can handle. Code after the failed statement in that try block is skipped. finally runs during cleanup whether an exception occurred or not. Avoid a bare except: it can hide programming errors and interrupts.',
    'text = "oops"\ntry:\n    number = int(text)\nexcept ValueError:\n    print("Not an integer")', 'Not an integer\n', 'branch',
    [step(3, 'int tries to parse the text.', ['oops', 'int', '?'], [1]), step(4, 'Invalid numeric text raises ValueError.', ['try', 'ValueError', 'except'], [1], [], [[0, 1], [1, 2]]), step(5, 'The matching handler supplies a helpful message.', ['Not an integer'], [0])],
    'Catching Exception around an entire program can conceal unrelated errors.', 'Safe integer',
    'Implement safe_int(text). Return the parsed integer, or None when int(text) raises ValueError.',
    'def safe_int(text):\n    pass', [case('safe_int("42")', 42, 'Valid'), case('safe_int(" -3 ")', -3, 'Signed'), case('safe_int("oops")', None, 'Invalid'), case('safe_int("")', None, 'Empty')],
    ['Wrap int(text) in a try block.', 'Catch ValueError and return None.'],
    'def safe_int(text):\n    try:\n        return int(text)\n    except ValueError:\n        return None', 'Only the expected parse failure is handled; unrelated exceptions remain visible.', ['text is always a string.'])

add('classes', 'Classes & objects', 'Group state and behavior into independent instances.',
    'A class describes objects with related data and behavior. __init__ initializes a new instance. self is the instance passed to a method call; attributes such as self.value belong to that instance. Separate instances can hold different state. Mutable class attributes are shared, so initialize per-instance lists inside __init__.',
    'class Counter:\n    def __init__(self):\n        self.value = 0\n    def increment(self):\n        self.value += 1\n\na = Counter()\nb = Counter()\na.increment()\nprint(a.value, b.value)', '1 0\n', 'bindings',
    [step(7, 'a refers to a Counter with its own value.', ['value: 0'], [0], ['a']), step(8, 'b is a distinct Counter instance.', ['value: 0', 'value: 0'], [1], ['a', 'b']), step(9, 'Calling a.increment changes only a.', ['value: 1', 'value: 0'], [0], ['a', 'b'])],
    'Forgetting self in a method definition produces confusing argument-count errors.', 'A simple counter',
    'Implement Counter with value initially 0. increment() increases value by one and returns the new value.',
    'class Counter:\n    def __init__(self):\n        pass\n\n    def increment(self):\n        pass', [case('Counter().value', 0, 'Initial state'), case('(lambda c: [c.increment(), c.increment(), c.value])(Counter())', [1, 2, 2], 'Repeated calls'), case('(lambda a,b: [a.increment(), b.value])(Counter(), Counter())', [1, 0], 'Independent instances')],
    ['Set self.value in __init__.', 'Increment self.value, then return it.'],
    'class Counter:\n    def __init__(self):\n        self.value = 0\n\n    def increment(self):\n        self.value += 1\n        return self.value', 'Instance attributes preserve state between calls and remain independent between objects.', ['No global counter; each instance is independent.'])

add('files-modules', 'Files & modules', 'Read a virtual file and reuse standard-library modules.',
    'with open(...) closes a file automatically when its block ends. Specify an encoding for text. import gives access to a module; for example math provides sqrt. Here files live in an isolated browser virtual workspace. They are not your computer\'s files and are reset between runs. data.txt is supplied as a fixture containing 3, 4, and 5 on separate lines.',
    'import math\nwith open("data.txt", encoding="utf-8") as file:\n    numbers = [int(line) for line in file]\nprint(sum(numbers))\nprint(math.sqrt(16))', '12\n4.0\n', 'flow',
    [step(2, 'Open the supplied virtual data.txt.', ['data.txt', '3\n4\n5'], [0]), step(3, 'Convert each line to an integer.', [3, 4, 5], [0, 1, 2]), step(4, 'The sum is 12; math supplies sqrt separately.', [12, 4.0], [0])],
    'open does not automatically access local computer files. A missing virtual path raises FileNotFoundError.', 'Total a file',
    'Implement total_file(path), reading one integer per line from a UTF-8 text file and returning the sum. Empty files sum to zero.',
    'def total_file(path):\n    pass', [case('total_file("data.txt")', 12, 'Three lines'), case('total_file("empty.txt")', 0, 'Empty file'), case('total_file("signed.txt")', -2, 'Signed integers')],
    ['Use with open(path, encoding="utf-8") as file.', 'Convert each line to int and accumulate it, or use sum.'],
    'def total_file(path):\n    with open(path, encoding="utf-8") as file:\n        return sum(int(line) for line in file)', 'The context manager closes the file, including if conversion raises an exception.', ['Files exist in the virtual workspace; each nonempty line is an integer.'])


add('complexity', 'Time & space complexity', 'Describe how work grows as the input grows.',
    'Big O describes growth, not a stopwatch measurement. Visiting n elements once takes O(n) time. Two full nested traversals take O(n²). A fixed number of counters uses O(1) auxiliary space; a new list of n results uses O(n). State what n means and whether you are discussing auxiliary or total space.',
    'numbers = [2, 4, 6, 8]\ntotal = 0\nfor number in numbers:\n    total += number\nprint(total)', '20\n', 'array',
    [step(4, 'One addition per element: total 2.', [2, 4, 6, 8], [0]), step(4, 'After two visits: total 6.', [2, 4, 6, 8], [1]), step(4, 'After four visits: total 20. Linear work, one accumulator.', [2, 4, 6, 8], [3])],
    'O(1) does not mean one instruction; it means a bound independent of input size.', 'Count positive values',
    'Implement count_positive(values) in one pass. Count values strictly greater than zero without building another list.',
    'def count_positive(values):\n    pass', [case('count_positive([-2, 0, 3, 4])', 2), case('count_positive([])', 0, 'Empty'), case('count_positive([0, -1])', 0, 'No positives')],
    ['Use an integer counter.', 'Increment the counter only for values > 0.'],
    'def count_positive(values):\n    count = 0\n    for value in values:\n        if value > 0:\n            count += 1\n    return count', 'One traversal gives O(n) time and O(1) auxiliary space.', ['At most 100 integers.'], track='dsa', prerequisites=['loops', 'functions', 'lists-tuples'])

add('linear-search', 'Linear search', 'Find a target by examining one element at a time.',
    'Linear search works on unsorted sequences. Visit indices from left to right and return as soon as the target matches. If no match appears, return -1 after the loop. The worst case examines all n items: O(n) time and O(1) auxiliary space.',
    'def linear_search(values, target):\n    for i, value in enumerate(values):\n        if value == target:\n            return i\n    return -1\n\nprint(linear_search([4, 2, 7, 1], 7))', '2\n', 'linear',
    [step(3, '4 does not match 7.', [4, 2, 7, 1], [0]), step(3, '2 does not match 7.', [4, 2, 7, 1], [1]), step(4, '7 matches at index 2.', [4, 2, 7, 1], [2])],
    'Returning -1 inside the loop stops after the first non-match.', 'First match',
    'Implement linear_search(values, target). Return the index of the first match or -1 if absent.',
    'def linear_search(values, target):\n    pass', [case('linear_search([4, 2, 7, 1], 7)', 2), case('linear_search([2, 2], 2)', 0, 'First duplicate'), case('linear_search([], 1)', -1, 'Empty'), case('linear_search([1], 2)', -1, 'Missing')],
    ['enumerate gives both the index and value.', 'Return -1 only after the loop finishes.'],
    'def linear_search(values, target):\n    for i, value in enumerate(values):\n        if value == target:\n            return i\n    return -1', 'An early return gives the first match and avoids unnecessary comparisons.', ['At most 100 integers.'], track='dsa')

add('binary-search', 'Binary search', 'Discard half of a sorted search interval at every step.',
    'Binary search requires sorted input. Track inclusive low and high indices. If the middle value is too small, the target can only be to its right; otherwise search left. Move past the examined midpoint to guarantee progress. Worst-case time is O(log n) with O(1) auxiliary space for this iterative implementation.',
    'def binary_search(values, target):\n    low, high = 0, len(values) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if values[mid] == target:\n            return mid\n        if values[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1\n\nprint(binary_search([1, 3, 5, 7, 9], 7))', '3\n', 'binary',
    [step(4, 'Search [0,4]; midpoint 2 holds 5.', [1, 3, 5, 7, 9], [2]), step(8, '5 < 7, so move low to 3.', [1, 3, 5, 7, 9], [3, 4]), step(6, 'Midpoint 3 holds the target.', [1, 3, 5, 7, 9], [3])],
    'Binary search on unsorted input can silently return a wrong answer.', 'Find in sorted values',
    'Implement binary_search(values, target) for ascending distinct integers. Return its index or -1.',
    'def binary_search(values, target):\n    pass', [case('binary_search([1, 3, 5, 7, 9], 7)', 3), case('binary_search([], 4)', -1, 'Empty'), case('binary_search([1], 1)', 0, 'One item'), case('binary_search([1, 4], 3)', -1, 'Between items')],
    ['Keep low and high as inclusive indices.', 'Update low = mid + 1 or high = mid - 1.'],
    'def binary_search(values, target):\n    low, high = 0, len(values) - 1\n    while low <= high:\n        mid = (low + high) // 2\n        if values[mid] == target:\n            return mid\n        if values[mid] < target:\n            low = mid + 1\n        else:\n            high = mid - 1\n    return -1', 'Each iteration either returns a match or strictly shrinks the candidate interval.', ['Sorted distinct integers, at most 100 items.'], track='dsa')

add('bubble-sort', 'Bubble sort', 'Move large values right through adjacent comparisons.',
    'Compare neighboring elements and swap when they are out of order. One pass places the largest remaining item at the right edge. Repeat with a shorter unsorted prefix. This simple version takes O(n²) time and sorts a copy using O(n) auxiliary space; the swapping itself is in place.',
    'def bubble_sort(values):\n    result = values.copy()\n    for end in range(len(result) - 1, 0, -1):\n        for i in range(end):\n            if result[i] > result[i + 1]:\n                result[i], result[i + 1] = result[i + 1], result[i]\n    return result\n\nprint(bubble_sort([4, 2, 3, 1]))', '[1, 2, 3, 4]\n', 'bubble',
    [step(5, 'Compare adjacent 4 and 2.', [4, 2, 3, 1], [0, 1]), step(6, 'Swap them; 4 moves right.', [2, 4, 3, 1], [0, 1]), step(6, 'Further swaps place 4 at the end of the first pass.', [2, 3, 1, 4], [3]), step(7, 'Repeat shorter passes until sorted.', [1, 2, 3, 4], [0, 1, 2, 3])],
    'Accessing i + 1 when i is the last index causes IndexError.', 'Adjacent swaps',
    'Implement bubble_sort(values), returning a sorted copy. Do not use sorted() or list.sort().',
    'def bubble_sort(values):\n    pass', [case('bubble_sort([4, 2, 3, 1])', [1, 2, 3, 4]), case('bubble_sort([2, -1, 2])', [-1, 2, 2], 'Duplicates'), case('bubble_sort([])', [], 'Empty')],
    ['Copy the input, then compare pairs at i and i + 1.', 'After each pass, the final unsorted position is settled.'],
    'def bubble_sort(values):\n    result = values.copy()\n    for end in range(len(result) - 1, 0, -1):\n        for i in range(end):\n            if result[i] > result[i + 1]:\n                result[i], result[i + 1] = result[i + 1], result[i]\n    return result', 'Adjacent swaps preserve all elements and gradually establish a sorted suffix.', ['At most 100 integers.'], track='dsa')

add('insertion-sort', 'Insertion sort', 'Grow a sorted prefix by inserting one value at a time.',
    'Imagine sorting playing cards. Take the next value, shift larger prefix values one position right, then place the held value in the gap. Worst-case time is O(n²); already sorted input takes O(n) comparisons. Returning a copy uses O(n) auxiliary space.',
    'def insertion_sort(values):\n    result = values.copy()\n    for i in range(1, len(result)):\n        key = result[i]\n        j = i - 1\n        while j >= 0 and result[j] > key:\n            result[j + 1] = result[j]\n            j -= 1\n        result[j + 1] = key\n    return result\n\nprint(insertion_sort([4, 2, 3, 1]))', '[1, 2, 3, 4]\n', 'insertion',
    [step(4, 'Hold 2 separately; prefix [4] is sorted.', [4, 2, 3, 1], [1]), step(7, 'Shift 4 right; the key 2 is still held.', [4, 4, 3, 1], [1]), step(9, 'Place 2 in the gap.', [2, 4, 3, 1], [0]), step(10, 'Continue to insert 3 and then 1.', [1, 2, 3, 4], [0, 1, 2, 3])],
    'Save the key before shifting; otherwise its original array slot may be overwritten.', 'Insert into order',
    'Implement insertion_sort(values), returning a sorted copy without sorted() or list.sort().',
    'def insertion_sort(values):\n    pass', [case('insertion_sort([4, 2, 3, 1])', [1, 2, 3, 4]), case('insertion_sort([3, 3, -2])', [-2, 3, 3]), case('insertion_sort([])', [])],
    ['Start at index 1; the first item is already a sorted prefix.', 'Shift while j >= 0 and result[j] > key, then write at j + 1.'],
    'def insertion_sort(values):\n    result = values.copy()\n    for i in range(1, len(result)):\n        key = result[i]\n        j = i - 1\n        while j >= 0 and result[j] > key:\n            result[j + 1] = result[j]\n            j -= 1\n        result[j + 1] = key\n    return result', 'The prefix remains sorted after every insertion.', ['At most 100 integers.'], track='dsa')

add('stacks-queues', 'Stacks & queues', 'Choose LIFO or FIFO to match the problem.',
    'A stack removes the most recently added item (LIFO); list.append and list.pop make a natural Python stack. A queue removes the oldest item (FIFO). collections.deque supports efficient append and popleft. list.pop(0) shifts remaining items and takes O(n), while deque.popleft takes O(1).',
    'from collections import deque\nstack = [1, 2, 3]\nprint(stack.pop())\nqueue = deque([1, 2, 3])\nprint(queue.popleft())', '3\n1\n', 'stack',
    [step(2, 'A stack adds and removes at the top.', [1, 2, 3], [2], ['bottom', '', 'top']), step(3, 'pop returns 3, leaving [1,2].', [1, 2], [1]), step(4, 'A queue preserves arrival order.', [1, 2, 3], [0], ['front', '', 'back']), step(5, 'popleft returns 1.', [2, 3], [0], ['front', 'back'])],
    'Popping an empty stack or queue raises IndexError; check whether it has items.', 'Balanced parentheses',
    'Implement balanced(text) for strings containing only ( and ). Return True if every opener is closed in the proper order.',
    'def balanced(text):\n    pass', [case('balanced("(()())")', True), case('balanced(")(")', False, 'Wrong order'), case('balanced("((")', False, 'Unclosed'), case('balanced("")', True, 'Empty')],
    ['Push open parentheses onto a stack.', 'A closer needs a matching opener; the stack must be empty at the end.'],
    'def balanced(text):\n    stack = []\n    for char in text:\n        if char == "(":\n            stack.append(char)\n        elif not stack:\n            return False\n        else:\n            stack.pop()\n    return not stack', 'Unmatched closers fail immediately; leftover openers fail at the end. O(n) time and O(n) worst-case space.', ['Only parentheses; length <= 100.'], track='dsa')

add('linked-lists', 'Linked-list fundamentals', 'Follow references rather than contiguous indices.',
    'A linked node stores a value and a reference to the next node. The head names the first node; None marks the end. Traversal follows next links and takes O(n). Reaching index k takes O(k), unlike list indexing. Inserting after a known node can update a constant number of links.',
    'head = {"value": 2, "next": {"value": 4, "next": {"value": 6, "next": None}}}\nnode = head\nwhile node is not None:\n    print(node["value"])\n    node = node["next"]', '2\n4\n6\n', 'linked',
    [step(2, 'head refers to the first node.', [2, 4, 6, 'None'], [0], [], [[0, 1], [1, 2], [2, 3]]), step(5, 'Follow next to the second node.', [2, 4, 6, 'None'], [1], [], [[0, 1], [1, 2], [2, 3]]), step(5, 'After 6, next is None and traversal ends.', [2, 4, 6, 'None'], [3], [], [[0, 1], [1, 2], [2, 3]])],
    'Forgetting to advance node leaves traversal stuck on the same object.', 'Collect linked values',
    'Implement linked_values(head). Nodes are dictionaries with value and next keys; return their values in traversal order.',
    'def linked_values(head):\n    pass', [case('linked_values({"value": 2, "next": {"value": 4, "next": None}})', [2, 4]), case('linked_values(None)', [], 'Empty'), case('linked_values({"value": 0, "next": None})', [0], 'One node')],
    ['Create a result list and start node at head.', 'Append node["value"] and then advance to node["next"].'],
    'def linked_values(head):\n    result = []\n    node = head\n    while node is not None:\n        result.append(node["value"])\n        node = node["next"]\n    return result', 'Traversal uses O(1) auxiliary state besides the O(n) returned list.', ['Acyclic chain with at most 100 nodes.'], track='dsa')

add('recursion', 'Recursion & the call stack', 'Solve a smaller problem and stop at a base case.',
    'A recursive function calls itself on a smaller problem. Each active call has its own local state on the call stack. A base case returns without another call. factorial(n) multiplies n by factorial(n-1), with factorial(0) = 1. Python does not eliminate tail calls and has a recursion limit.',
    'def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(3))', '6\n', 'recursion',
    [step(4, 'factorial(3) waits for factorial(2).', ['f(3)', 'f(2)'], [1]), step(4, 'Calls continue down to zero.', ['f(3)', 'f(2)', 'f(1)', 'f(0)'], [3]), step(3, 'Base case returns 1; waiting calls resume.', ['3 × ?', '2 × ?', '1 × 1'], [2]), step(6, 'Unwind: 1, then 2, then 6.', [6], [0])],
    'Missing a base case or failing to shrink the input eventually causes RecursionError.', 'Recursive factorial',
    'Implement factorial(n) recursively for non-negative integers. Return 1 for n = 0.',
    'def factorial(n):\n    pass', [case('factorial(0)', 1, 'Base case'), case('factorial(1)', 1), case('factorial(5)', 120)],
    ['Handle n == 0 before recursing.', 'Return n * factorial(n - 1) otherwise.'],
    'def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n - 1)', 'There are n+1 calls: O(n) time and O(n) stack space.', ['0 <= n <= 12.'], track='dsa', prerequisites=['functions', 'conditions'])

add('merge-sort', 'Merge sort', 'Divide, sort the halves, then merge them.',
    'Split a list until pieces have at most one item. Recursively sort the two halves. Merge by repeatedly taking the smaller front item, then append the remaining tail. Merge sort takes O(n log n) time. This Python implementation uses slices and new lists, with O(n) peak auxiliary storage plus an O(log n) call stack.',
    'def merge_sort(values):\n    if len(values) <= 1:\n        return values.copy()\n    mid = len(values) // 2\n    left = merge_sort(values[:mid])\n    right = merge_sort(values[mid:])\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    return result + left[i:] + right[j:]\n\nprint(merge_sort([4, 2, 3, 1]))', '[1, 2, 3, 4]\n', 'merge',
    [step(4, 'Split into [4,2] and [3,1].', [4, 2, 3, 1], [0, 1]), step(3, 'Singletons are already sorted.', [4, 2, 3, 1], [0]), step(16, 'Merge each pair into [2,4] and [1,3].', [2, 4, 1, 3], [0, 1]), step(16, 'Merge both sorted halves.', [1, 2, 3, 4], [0, 1, 2, 3])],
    'Do not forget the unconsumed tail after one half runs out.', 'Merge two sorted lists',
    'Implement merge(left, right), returning one sorted list containing all values. Preserve duplicates and do not mutate inputs.',
    'def merge(left, right):\n    pass', [case('merge([1, 4], [2, 3])', [1, 2, 3, 4]), case('merge([], [1])', [1], 'Empty half'), case('merge([2, 2], [2])', [2, 2, 2], 'Duplicates')],
    ['Use separate indices i and j.', 'Append the smaller value and advance only its index; append both tails afterward.'],
    'def merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    return result + left[i:] + right[j:]', 'Every element enters the output once: O(n+m) time and output space.', ['Both inputs sorted ascending; at most 100 total integers.'], track='dsa', prerequisites=['recursion', 'lists-tuples'])

add('trees', 'Tree traversal', 'Visit a hierarchy in a deliberate order.',
    'A binary tree node has at most two children. Preorder visits node, left, right. Inorder visits left, node, right. Postorder visits left, right, node. Inorder is sorted only when the tree satisfies the binary-search-tree ordering rule. Traversing n nodes takes O(n) time; recursion needs O(h) stack space for height h.',
    'def inorder(node):\n    if node is None:\n        return []\n    return inorder(node["left"]) + [node["value"]] + inorder(node["right"])\n\ntree = {"value": 2, "left": {"value": 1, "left": None, "right": None}, "right": {"value": 3, "left": None, "right": None}}\nprint(inorder(tree))', '[1, 2, 3]\n', 'tree',
    [step(4, 'Visit the left subtree first.', [2, 1, 3], [1], [], [[0, 1], [0, 2]]), step(4, 'Then visit the root.', [2, 1, 3], [0], [], [[0, 1], [0, 2]]), step(4, 'Finally visit the right subtree.', [2, 1, 3], [2], [], [[0, 1], [0, 2]])],
    'A tree is not automatically a binary search tree. Structure alone does not guarantee sorted traversal.', 'Preorder values',
    'Implement preorder(node) for dictionary nodes with value, left, and right. Return values in root-left-right order; None is an empty tree.',
    'def preorder(node):\n    pass', [case('preorder(None)', [], 'Empty'), case('preorder({"value": 2, "left": {"value": 1, "left": None, "right": None}, "right": {"value": 3, "left": None, "right": None}})', [2, 1, 3], 'Three nodes')],
    ['Handle None as the base case.', 'Append root, then recursively visit left and right using one accumulator.'],
    'def preorder(node):\n    result = []\n    def visit(current):\n        if current is None:\n            return\n        result.append(current["value"])\n        visit(current["left"])\n        visit(current["right"])\n    visit(node)\n    return result', 'One shared output list avoids repeated list concatenation. The teaching inorder example is concise, but concatenation can add copying cost on deep trees.', ['Acyclic binary tree with at most 50 nodes.'], track='dsa', prerequisites=['recursion', 'dictionaries-sets'])

add('graph-bfs', 'Graphs & breadth-first search', 'Explore reachable nodes one layer at a time.',
    'An adjacency list maps each node to its neighbors. BFS uses a queue and marks nodes visited when enqueueing them, avoiding duplicates and cycles. With adjacency lists and a set, traversal is O(V+E) over reachable vertices and edges. BFS finds shortest edge-count distances in unweighted graphs.',
    'from collections import deque\ndef bfs(graph, start):\n    queue = deque([start])\n    seen = {start}\n    order = []\n    while queue:\n        node = queue.popleft()\n        order.append(node)\n        for neighbor in graph.get(node, []):\n            if neighbor not in seen:\n                seen.add(neighbor)\n                queue.append(neighbor)\n    return order\n\nprint(bfs({"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "A"))', "['A', 'B', 'C', 'D']\n", 'graph',
    [step(7, 'Dequeue A; enqueue B then C.', ['A', 'B', 'C', 'D'], [0], [], [[0, 1], [0, 2], [1, 3]]), step(7, 'Dequeue B; enqueue D behind C.', ['A', 'B', 'C', 'D'], [1], [], [[0, 1], [0, 2], [1, 3]]), step(7, 'C is next, followed by D.', ['A', 'B', 'C', 'D'], [2], [], [[0, 1], [0, 2], [1, 3]]), step(13, 'Queue exhausted: A, B, C, D.', ['A', 'B', 'C', 'D'], [3], [], [[0, 1], [0, 2], [1, 3]])],
    'Without a seen set, a cycle can cause repeated visits forever.', 'Breadth-first order',
    'Implement bfs(graph, start). Follow neighbors in their supplied list order and return each reachable node once.',
    'from collections import deque\n\ndef bfs(graph, start):\n    pass', [case('bfs({"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "A")', ['A', 'B', 'C', 'D']), case('bfs({"A": ["B"], "B": ["A"]}, "A")', ['A', 'B'], 'Cycle'), case('bfs({}, "X")', ['X'], 'Isolated start')],
    ['Use deque and popleft for FIFO behavior.', 'Mark each neighbor seen before appending it to the queue.'],
    'from collections import deque\ndef bfs(graph, start):\n    queue = deque([start])\n    seen = {start}\n    order = []\n    while queue:\n        node = queue.popleft()\n        order.append(node)\n        for neighbor in graph.get(node, []):\n            if neighbor not in seen:\n                seen.add(neighbor)\n                queue.append(neighbor)\n    return order', 'Seen-on-enqueue ensures each reachable node enters the queue once.', ['At most 20 string nodes; missing keys have no outgoing neighbors.'], track='dsa', prerequisites=['stacks-queues', 'dictionaries-sets'])

add('graph-dfs', 'Depth-first search', 'Follow one branch deeply before backtracking.',
    'DFS explores a neighbor recursively before trying the next neighbor. A seen set makes it safe for graphs with cycles. It is useful for reachability and structural analysis, but unlike BFS does not generally find shortest paths. Recursive DFS uses up to O(V) call-stack space and O(V+E) traversal time.',
    'def dfs(graph, start):\n    seen = set()\n    order = []\n    def visit(node):\n        if node in seen:\n            return\n        seen.add(node)\n        order.append(node)\n        for neighbor in graph.get(node, []):\n            visit(neighbor)\n    visit(start)\n    return order\n\nprint(dfs({"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "A"))', "['A', 'B', 'D', 'C']\n", 'graph',
    [step(8, 'Visit A and descend to B.', ['A', 'B', 'C', 'D'], [0], [], [[0, 1], [0, 2], [1, 3]]), step(10, 'From B, descend to D before considering C.', ['A', 'B', 'C', 'D'], [1, 3], [], [[0, 1], [0, 2], [1, 3]]), step(10, 'Backtrack to A, then visit C.', ['A', 'B', 'C', 'D'], [2], [], [[0, 1], [0, 2], [1, 3]])],
    'Mark a node seen before visiting its neighbors, not after returning from them.', 'Depth-first order',
    'Implement dfs(graph, start) with recursive neighbor-list order. Return each reachable node once.',
    'def dfs(graph, start):\n    pass', [case('dfs({"A": ["B", "C"], "B": ["D"], "C": [], "D": []}, "A")', ['A', 'B', 'D', 'C']), case('dfs({"A": ["B"], "B": ["A"]}, "A")', ['A', 'B'], 'Cycle'), case('dfs({}, "X")', ['X'], 'Isolated')],
    ['Keep seen and order outside a nested visit function.', 'In visit, skip seen nodes, record this node, then visit each neighbor.'],
    'def dfs(graph, start):\n    seen = set()\n    order = []\n    def visit(node):\n        if node in seen:\n            return\n        seen.add(node)\n        order.append(node)\n        for neighbor in graph.get(node, []):\n            visit(neighbor)\n    visit(start)\n    return order', 'The call stack remembers where to resume when a deeper branch ends.', ['At most 20 string nodes; missing keys have no outgoing neighbors.'], track='dsa', prerequisites=['graph-bfs', 'recursion'])
