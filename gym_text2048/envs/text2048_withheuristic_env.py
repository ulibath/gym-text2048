import logging

import numpy as np

from gym_text2048.envs import Text2048Env


logger = logging.getLogger(__name__)


class Text2048WithHeuristicEnv(Text2048Env):
    def __init__(self, size=4, merge_weight=0., empty_weight=0.,
                 monotonicity_weight=0., monotonicity_exp=1.,
                 sum_weight=0., sum_exp=1., shift_weight=0.):
        self.merge_weight = merge_weight
        self.empty_weight = empty_weight
        self.monotonicity_weight = monotonicity_weight
        self.monotonicity_exp = monotonicity_exp
        self.sum_weight = sum_weight
        self.sum_exp = sum_exp
        self.shift_weight = shift_weight
        super(Text2048WithHeuristicEnv, self).__init__(size=size)

    def _calculate_state_value(self):
        # Sum of the logs of the tile values
        tile_sum = np.sum(np.power(self.board, self.sum_exp))

        # Count zeros on the board
        empty = self.size * self.size - np.count_nonzero(self.board)
        if empty > (self.size * self.size * 3/4):
                self.moved_cells = 0

        # Count possible merges on the board
        def count_merges(line):
            count, merge, prev = 0, 0, 0
            for value in line:
                if value != 0 and value == prev:
                    count += 1
                elif count > 0:
                    merge += (1 + count) * prev
                    count = 0
                prev = value
            if count > 0:
                merge += (1 + count) * prev
            return merge

        # NOTE: maybe try taking the maximum of the lines and columns instead
        merges = sum([count_merges(self.board[i]) for i in range(self.size)])
        merges += sum([count_merges(self.board[:,j]) for j in range(self.size)])

        # Score the monotonicity of each row and column
        # Count only if they are subsequent values
        # Higher values get higher scores
        def score_monotonicity(line):
            left, right = 0., 0.
            for i in range(self.size):
                if abs(line[i-1] - line[i] == 1):
                    if line[i-1] > line[i]:
                        left += 1 #pow(line[i], self.monotonicity_exp)
                    else:
                        right += 1 #pow(line[i-1], self.monotonicity_exp)
            # NOTE: original code from github.com/nneonneo/2048-ai/ uses min
            # instead of max. This doesn't seem to reward the correct behaviour
            return max(left, right)

        monotonicity = sum([score_monotonicity(self.board[i]) for i in range(self.size)])
        monotonicity += sum([score_monotonicity(self.board[:][j]) for j in range(self.size)])

        # Count number of shifted tiles as penality
        # shifts = np.sum(self.board == self.prev_board)
        # print(f'mono: {monotonicity}, empty: {empty}, merges: {merges}, shifts: {self.moved_cells}, tilesum: {tile_sum}')
        # Return weighted sum of heuristic scores
        return (self.empty_weight * empty +
                self.merge_weight * merges +
                self.monotonicity_weight * monotonicity +
                self.sum_weight * tile_sum -
                self.shift_weight * self.moved_cells)

    def _get_reward(self):
        curr_value = self._calculate_state_value()
        prev_value = self.last_state_value
        # self.last_state_value = curr_value
        return self.last_action_score + curr_value #- prev_value

    def reset(self):
        obs = super(Text2048WithHeuristicEnv, self).reset()
        self.last_state_value = self._calculate_state_value()
        return obs
