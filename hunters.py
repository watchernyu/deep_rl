'''
    This is a multi-agent learning task, where k hunters (agents) are trying to
    catch m rabbits in an nxn grid.

    Hunters and rabbits are initialized randomly on the grid, with overlaps.
    An episode ends when all rabbits have been captured. Rabbits can have
    different movement patterns. There is a reward of -1 per time step.

    States are size 2*k+2*m flattened arrays of:
      concat(hunter positions, rabbit positions)
    Positions are of the form:
      [0, 0] = top-left, [n-1, n-1] = top-bottom, [-1, -1] = removed

    Actions are size 2*k flattened arrays of:
      concat(hunter 1 movement, hunter 2 movement, ..., hunter k movement)
    Movements are of the form:
      [0, 1] = right, [-1, 1] = up-right, [0, 0] = stay, etc
'''

import numpy as np

n = 6  # grid size
k = 3  # hunters
m = 3  # rabbits

def initial_state():
    '''Returns a randomly initial state. The state vector is a flat array of:
        concat(hunter positions, rabbit positions).'''
    return np.random.randint(0, n, size=2*k+2*m)

def valid_state(s):
    '''Returns if the given state vector is valid.'''
    return s.shape == (2*k+2*m, ) and np.all([-1 <= e < n for e in s])

def valid_action(a):
    '''Returns if the given action vector is valid'''
    return a.shape == (2*k, ) and np.all([-1 <= e <= 1 for e in a])

def perform_action(s, a, rabbit_action=None, remove_hunter=False):
    '''Performs action a in state s.

       Parameters:
       s is the state vector
       a is the action vector
       rabbit_action is either
         None: rabbits do not move
         'random': rabbits move one block randomly
         'opposite': rabbits move opposite to the closest hunter
       remove_hunter will remove the first hunter that captures a rabbit

       Returns:
       (s_next, reward, is_end)'''
    assert valid_state(s)
    assert valid_action(a)

    # Calculate rabbit actions
    if rabbit_action is None:
        rabbit_a = np.zeros(2*m, dtype=np.int)
    elif rabbit_action == 'random':
        rabbit_a = np.random.randint(-1, 2, size=2*m)
    elif rabbit_action == 'opposite':
        rabbit_a = np.zeros(2*m, dtype=np.int)
        for i in range(0, 2*m, 2):
            rabbit_a[i:i+2] = opposite_direction(s, a, 2*k+i)
    else:
        raise ValueError('Invalid rabbit_action')

    # Get positions after hunter and rabbit actions
    a = np.concatenate((a, rabbit_a))
    positions = np.zeros(len(s), dtype=np.int)
    for i in range(len(s)):
        if s[i] == -1:
            positions[i] = s[i]
        elif 0 <= s[i] + a[i] < n:
            positions[i] = s[i] + a[i]
        else:
            positions[i] = s[i]

    # Remove rabbits (and optionally hunters) that overlap
    hunter_pos, rabbit_pos = positions[:2*k], positions[2*k:]
    for i in range(0, len(hunter_pos), 2):
        hunter = hunter_pos[i:i+2]
        for j in range(0, len(rabbit_pos), 2):
            rabbit = rabbit_pos[j:j+2]
            if (hunter == rabbit).all():
                rabbit_pos[j:j+2] = [-1, -1]
                if remove_hunter: hunter_pos[i:i+2] = [-1, -1]

    # Return (s_next, reward, is_end)
    s_next = np.concatenate((hunter_pos, rabbit_pos))
    is_end = (rabbit_pos == -1).all()
    return s_next, -1, is_end

def opposite_direction(s, a, i):
    '''Returns the direction the rabbit at s[i], s[i+1] should move to avoid
       the closest hunter (after hunters take action a).
    '''
    # Calculate hunter positions after a
    hunter_s = np.array(s[:2*k])
    for j in range(2*k):
        if hunter_s[j] == -1:
            continue
        elif 0 <= hunter_s[j] + a[j] < n:
            hunter_s[j] += a[j]

    # Find position of closest hunter
    rabbit = s[i:i+2]
    distance = float('inf')
    for j in range(0, 2*k, 2):
        d = np.linalg.norm(rabbit - s[j:j+2])
        if d < distance:
            closest_hunter = s[j:j+2]
    
    # Calculate opposite direction
    return np.sign(rabbit - closest_hunter)
