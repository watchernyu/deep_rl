'''
    This is a multi-agent learning task, where k hunters (agents) are trying to
    catch m rabbits in an nxn grid.

    Hunters and rabbits are initialized randomly on the grid, with overlaps.
    An episode ends when all rabbits have been captured. Rabbits can have
    different movement patterns. There is a reward of -1 per time step (and
    optionally a +1 reward on capturing a rabbit).

    States are size 3*k+3*m flattened arrays of:
      concat(hunter positions, rabbit positions)
    Positions are of the form:
      [in-game, y-position, x-position], so
      [1, 0, 0] = top-left, [1, 0, n-1] = top-right, [0, -1, -1] = removed

    Actions are size 2*k flattened arrays of:
      concat(hunter 1 movement, hunter 2 movement, ..., hunter k movement)
    Movements are of the form:
      [0, 1] = right, [-1, 1] = up-right, [0, 0] = stay, etc
'''

import numpy as np


class GameOptions(object):

    def __init__(self, num_hunters=None, num_rabbits=None, grid_size=None, timestep_reward=None, capture_reward=None):

        self.num_hunters = num_hunters
        self.num_rabbits = num_rabbits
        self.grid_size = grid_size
        self.timestep_reward = timestep_reward
        self.capture_reward = capture_reward


class RabbitHunter(object):

    action_space = [
        np.array([-1, -1]), np.array([-1, 0]), np.array([-1, 1]),
        np.array([0, -1]), np.array([0, 0]), np.array([0, 1]),
        np.array([1, -1]), np.array([1, 0]), np.array([1, 1])
    ]

    def __init__(self, options):
        self.set_options(options)
        print(options.__dict__)

    def set_options(self, options):
        self.num_hunters = options.num_hunters
        self.num_active_hunters = options.num_hunters

        self.num_rabbits = options.num_rabbits
        self.num_active_rabbits = options.num_rabbits

        self.num_agents = self.num_hunters + self.num_rabbits
        self.num_active_agents = self.num_active_hunters + self.num_active_rabbits

        self.grid_size = options.grid_size
        self.timestep_reward = options.timestep_reward
        self.capture_reward = options.capture_reward

    def start_state(self):
        '''Returns a random initial state. The state vector is a flat array of:
           concat(hunter positions, rabbit positions).'''

        start = np.random.randint(0, self.grid_size, size=3 * self.num_hunters + 3 * self.num_rabbits)
        start[::3] = 1

        return start

    def perform_action(self, state, a_indices):
        '''Performs an action given by a_indices in state s. Returns:
           (s_next, reward)'''
        a = action_indices_to_coordinates(a_indices)
        # print(a)

        # Get positions after hunter and rabbit actions
        # a = np.concatenate((a, rabbit_a))
        hunter_pos = np.zeros(self.num_active_hunters * 3, dtype=np.int)
        for hunter in range(0, self.num_active_hunters):
            hunter_idx = hunter * 3
            if state[hunter_idx] == 0:
                hunter_pos[hunter_idx:hunter_idx + 3] = [0, -1, -1]
            else:
                hunter_pos[hunter_idx] = 1
                hunter_act = a[hunter_idx - hunter:hunter_idx - hunter + 2]
                # print(hunter_act)
                sa = state[hunter_idx + 1:hunter_idx + 3] + hunter_act
                # print(sa)
                clipped = np.clip(sa, 0, self.grid_size - 1)
                # print(clipped)
                # print(hunter_pos[hunter_idx + 1:hunter_idx + 3])
                hunter_pos[hunter_idx + 1:hunter_idx + 3] = clipped

        # Remove rabbits (and optionally hunters) that overlap
        reward = self.timestep_reward
        rabbit_pos = state[self.num_active_hunters * 3:]

        captured_rabbit_idxes = []
        inactive_hunter_idxes = []
        for i in range(0, len(hunter_pos), 3):
            hunter = hunter_pos[i:i + 3]
            for j in range(0, len(rabbit_pos), 3):
                rabbit = rabbit_pos[j:j + 3]
                if hunter[0] == 1 and rabbit[0] == 1 and array_equal(hunter, rabbit):
                    # A rabbit has been captured
                    # Remove captured rabbit and respective hunter
                    rabbit_pos[j:j + 3] = [0, -1, -1]
                    captured_rabbit_idxes += [j, j + 1, j + 2]
                    reward += self.capture_reward
                    hunter_pos[i:i + 3] = [0, -1, -1]
                    inactive_hunter_idxes += [i, i + 1, i + 2]

        rabbit_pos = np.delete(rabbit_pos, captured_rabbit_idxes, axis=0)
        hunter_pos = np.delete(hunter_pos, inactive_hunter_idxes, axis=0)
        self.num_active_hunters -= int(len(inactive_hunter_idxes) / 3)
        self.num_active_rabbits -= int(len(captured_rabbit_idxes) / 3)

        # Return (s_next, reward)
        s_next = np.concatenate((hunter_pos, rabbit_pos))

        return s_next, reward

    def filter_actions(self, state, agent_no):
        '''Filter the actions available for an agent in a given state. Returns a
           bitmap of available actions. Hunter should be active.
           E.g. an agent in a corner is not allowed to move into a wall.'''
        avail_a = np.ones(9, dtype=int)
        hunter_pos = state[3 * agent_no + 1:3 * agent_no + 3]

        for i in range(len(RabbitHunter.action_space)):
            # Check if action moves us off the grid
            a = RabbitHunter.action_space[i]
            sa = hunter_pos + a
            if (sa[0] < 0 or sa[0] >= self.grid_size) or (sa[1] < 0 or sa[1] >= self.grid_size):
                avail_a[i] = 0
        return avail_a

    def is_end(self, state):
        '''Given a state, return if the game should end.'''
        if len(state) == 0:
            return True
        return False

def action_indices_to_coordinates(a_indices):
    '''Converts a list of action indices to action coordinates.'''
    coords = [RabbitHunter.action_space[i] for i in a_indices]
    return np.concatenate(coords)

def array_equal(a, b):
    '''Because np.array_equal() is too slow. Three-element arrays only.'''
    return a[0] == b[0] and a[1] == b[1] and a[2] == b[2]

# def valid_state(s):
#     '''Returns if the given state vector is valid.'''
#     return s.shape == (3*k+3*m, ) and \
#            np.all([-1 <= e < n for e in s]) and \
#            np.all([e in (0, 1) for e in s[::3]])

# def valid_action(a):
#     '''Returns if the given action vector is valid'''
#     return a.shape == (2*k, ) and np.all([-1 <= e <= 1 for e in a])

