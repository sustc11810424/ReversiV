
import numpy as np
import random
from time import perf_counter
import threading
rng = np.random.default_rng()
WEIGHT50 = np.array([
    [ 0.98541204,  0.04035845,  0.04384775,  0.04191742,  0.04185729, 0.04486757,  0.04413301,  0.97116454],
       
    [ 0.04848264, -0.30446803, -0.11258063, -0.05608972, -0.05857577,-0.11605463, -0.30616653,  0.0405198 ],
    
    [ 0.04045199, -0.11835686,  0.00369619, -0.01073905, -0.013084  , 0.005706  , -0.11639149,  0.03769541],
       
    [ 0.05197595, -0.06659195, -0.01282388,  0.01832268,  0.0205201 ,-0.01321658, -0.06568969,  0.04408597],
    
    [ 0.05241211, -0.0599413 , -0.01134043,  0.02166829,  0.01608053,-0.01993317, -0.06629244,  0.04791857],
    
    [ 0.05366062, -0.11717497,  0.01329587, -0.01950666, -0.01219502,0.0036302 , -0.11091427,  0.04376664],
        
    [ 0.05751975, -0.29662156, -0.11206735, -0.0714942 , -0.06593978,-0.11826274, -0.3029509 ,  0.04539823],
    
    [ 0.99039419,  0.03853371,  0.0364874 ,  0.03694624,  0.04121141,0.03857323,  0.04190149,  0.97900956],
])

DIR = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)) # 方向向量

INF = 1e10

def place(board, x, y, color):
        if x < 0:
            return True
        board[x][y] = color
        valid = False
        for d in range(8):
            i = x + DIR[d][0]
            j = y + DIR[d][1]
            while 0 <= i and i < 8 and 0 <= j and j < 8 and board[i][j] == -color:
                i += DIR[d][0]
                j += DIR[d][1]
            if 0 <= i and i < 8 and 0 <= j and j < 8 and board[i][j] == color:
                while True:
                    i -= DIR[d][0]
                    j -= DIR[d][1]
                    if i == x and j == y:
                        break
                    valid = True
                    board[i][j] = color
        return valid
def test_place(board, x, y, color):
    for d in range(8):
        i = x + DIR[d][0]
        j = y + DIR[d][1]
        while 0 <= i and i < 8 and 0 <= j and j < 8 and board[i][j] == -color:
            i += DIR[d][0]
            j += DIR[d][1]
        if  0 <= i and i < 8 and 0 <= j and j < 8 and board[i][j] == color:
            i -= DIR[d][0]
            j -= DIR[d][1]
            if not(i == x and j == y):
                return True
    return False

def find_move(board, color):
    moves = []
    for i in range(8):
        for j in range(8):
            if board[i][j] == 0:
                if test_place(board, i, j, color):
                    moves.append((i, j))
    return moves

def game_ended(board):
    if find_move(board, 1) or find_move(board,-1):
        return 0
    else:
        if board.sum()==0:
            return 0.1
        return board.sum() 

def eval(board):
    return np.sum(WEIGHT50*board)

def house_keeping(Qsa, Nsa, Ns, Es, Vs, turn):
    try:
        for s in list(Vs.keys()):
            if np.count_nonzero(np.fromstring(s,dtype=np.int))<turn:
                del Vs[s]
                del Ns[s]
                del Es[s]
        for s,a in list(Nsa.keys()):
            if np.count_nonzero(np.fromstring(s,dtype=np.int))<turn:
                del Nsa[(s,a)]
                del Qsa[(s,a)] 
    except KeyError:
        pass
    
#don't change the class name
class AI(object):
    #chessboard_size, color, time_out passed from agent
    def __init__(self, chessboard_size=8, color=-1, time_out=4.0, fn=eval):
        self.chessboard_size = chessboard_size
        self.color = color
        self.time_out = time_out-0.2
        self.candidate_list = []

        self.repeated = 0
        self.state_searched = 0
        self.cpuct = 1.2

        self.Qsa = {}  # stores Q values for s,a (as defined in the paper)
        self.Nsa = {}  # stores #times edge s,a was visited
        self.Ns = {}  # stores #times board s was visited
        self.Es = {}  # stores game.getGameEnded ended for board s
        self.Vs = {}  # stores game.getValidMoves for board s

# The input is current chessboard.
    def go(self, chessboard):
        # Clear candidate_list, must do this step
        self.repeated = 0
        self.state_searched = 0
        self.candidate_list.clear()
        self.candidate_list = find_move(chessboard, self.color)
        if self.candidate_list:
            # start = perf_counter()
            turn = np.count_nonzero(chessboard)-3
            if turn>48:
                self.candidate_list.append(self.alpha_beta(chessboard))
            else:
                self.candidate_list.append(self.MCTS(chessboard*self.color))
                threading.Thread(target=house_keeping, args=(self.Qsa, self.Nsa, self.Ns, self.Es, self.Vs, turn)).start()
            # print('player=%d time=%f turn=%d state searched=%d repeated=%d'%(self.color,perf_counter()-start,turn,self.state_searched,self.repeated))
        
        
    def alpha_beta(self, board):
        def max_value(board, color):
            s= (board*color).tostring() 
            self.state_searched+=1
            if s in self.Vs:
                self.repeated+=1
            else:
                self.Vs[s] = find_move(board, color)
            moves = self.Vs[s]
            if not moves:
                if not find_move(board, -color):
                    return np.sum(board)*self.color # ?
                else: 
                    return min_value(board.copy(), -color)
            try:
                moves.sort(key=lambda move: self.Nsa[(s, move)], reverse=True)
            except KeyError:
                moves.sort(key=lambda move: WEIGHT50[move[0],move[1]], reverse=True)
            v = -INF
            for x, y in moves:
                next_board = board.copy()
                assert place(next_board, x, y, color)
                v = max(v, min_value(next_board, -color))
                if v>0:
                    return v
            return v
        def min_value(board, color):
            s= (board*color).tostring() 
            self.state_searched+=1
            if s in self.Vs:
                self.repeated+=1
            else:
                self.Vs[s] = find_move(board, color)
            moves = self.Vs[s]
            if not moves:
                if not find_move(board, -color):
                    return np.sum(board)*self.color
                else:
                    return max_value(board.copy(), -color)
            try:
                moves.sort(key=lambda move: self.Nsa[(s, move)], reverse=True)
            except KeyError:
                moves.sort(key=lambda move: WEIGHT50[move[0],move[1]], reverse=True)
            v = INF
            for x, y in moves:
                next_board = board.copy()
                assert place(next_board, x, y, color)
                v = min(v, max_value(next_board, -color))
                if v<0:
                    return v
            return v

        moves = find_move(board, self.color)
        s = (board*self.color).tostring()
        try:
            moves.sort(key=lambda move: self.Nsa[(s, move)], reverse=True)
        except KeyError:
            moves.sort(key=lambda move: WEIGHT50[move[0],move[1]], reverse=True)
        for x, y in moves:
            next_board = board.copy()
            assert place(next_board, x, y, self.color)
            v = min_value(next_board, -self.color)
            if v> 0:
                return(x ,y)
        return moves[0]
    

    def MCTS(self, canonicalBoard):
        start_time = perf_counter()
        # search until run out of time
        count = 0
        while perf_counter() - start_time < self.time_out:
            self._search(canonicalBoard)
            count+=1
        s = canonicalBoard.tostring()
        
        moves = self.Vs[s]
        values = [self.Qsa[(s, a)] for a in moves]
        best_move = np.argmax(values)
        counts = [self.Nsa[(s, a)] for a in moves]
        best_move = np.argmax(counts)
        return moves[best_move]
        # counts = np.array([self.Nsa[(s, a)] for a in moves], dtype=np.float)
        # print(counts)
        # counts = counts*counts
        # print(counts, counts.sum())
        # counts/=counts.sum()
        # print(counts)
        # best_move = rng.choice(moves, p=counts)
        # return best_move

    def _search(self, canonicalBoard):
        s = canonicalBoard.tostring()
        if s not in self.Es:
            self.Es[s] = game_ended(canonicalBoard)
        if self.Es[s] != 0:
            # terminal node
            return -self.Es[s]

        if s not in self.Ns:
            # leaf node
            v = self.eval(canonicalBoard)
            moves = find_move(canonicalBoard, 1)
            self.Vs[s] = moves
            self.Ns[s] = 0
            return -v
        
        moves = self.Vs[s]
        cur_best = -float('inf')
        best_act = (-1, -1)
        if moves: p = 1.0/len(moves)
        # pick the action with the highest upper confidence bound
        for a in moves:
            if (s, a) in self.Qsa:
                u = self.Qsa[(s, a)] + self.cpuct * p * np.sqrt(self.Ns[s]) / (
                            1 + self.Nsa[(s, a)])
            else:
                u = self.cpuct * p * np.sqrt(self.Ns[s] + 1e-8)  
            if u > cur_best:
                cur_best = u
                best_act = a

        next_board = canonicalBoard.copy()
        assert place(next_board, best_act[0], best_act[1], 1)
        v = self._search(-next_board)
        a = best_act
        if (s, a) in self.Qsa:
            self.Qsa[(s, a)] = (self.Nsa[(s, a)] * self.Qsa[(s, a)] + v) / (self.Nsa[(s, a)] + 1)
            self.Nsa[(s, a)] += 1
        else:
            self.Qsa[(s, a)] = v
            self.Nsa[(s, a)] = 1
    
        self.Ns[s] += 1
        return -v
            

    