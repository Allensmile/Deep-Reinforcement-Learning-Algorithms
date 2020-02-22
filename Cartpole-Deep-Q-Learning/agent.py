
BATCH_SIZE = 64  
LEARNING_RATE = 0.001

import torch
import torch.optim as optim
import random
from model import QNetwork

use_cuda = torch.cuda.is_available()
FloatTensor = torch.cuda.FloatTensor if use_cuda else torch.FloatTensor

device = torch.device("cuda" if use_cuda else "cpu")
from  torch.autograd import Variable

from replay_buffer import ReplayMemory, Transition


class Agent(object):

    def __init__(self, n_states, n_actions, hidden_dim):
        """Agent class that choose action and train

        Args:
            input_dim (int): input dimension
            output_dim (int): output dimension
            hidden_dim (int): hidden dimension
        """
        
        self.q_local = QNetwork(n_states, n_actions, hidden_dim=16).to(device)
        self.q_target = QNetwork(n_states, n_actions, hidden_dim=16).to(device)
        
        self.mse_loss = torch.nn.MSELoss()
        self.optim = optim.Adam(self.q_local.parameters(), lr=LEARNING_RATE)
        
        self.n_states = n_states
        self.n_actions = n_actions

        #  ReplayMemory: trajectory is saved here
        self.replay_memory = ReplayMemory(10000)
        

    def get_action(self, state, eps, check_eps=True):
        """Returns an action

        Args:
            state : 2-D tensor of shape (n, input_dim)
            eps (float): eps-greedy for exploration

        Returns: int: action index
        """
        global steps_done
        sample = random.random()

        if check_eps==False or sample > eps:
           with torch.no_grad():
               # t.max(1) will return largest column value of each row.
               # second column on max result is index of where max element was
               # found, so we pick action with the larger expected reward.
               ## UserWarning: volatile was removed and now has no effect. 
               ## Use `with torch.no_grad():` instead.
               return self.q_local(Variable(state).type(FloatTensor)).data.max(1)[1].view(1, 1)
        else:
           ## return LongTensor([[random.randrange(2)]])
           return torch.tensor([[random.randrange(self.n_actions)]], device=device) 


    def learn(self, experiences, gamma):
        """Prepare minibatch and train them

        Args:
        experiences (List[Transition]): Minibatch of `Transition`
        gamma (float): Discount rate of Q_target
        """
        
        if len(self.replay_memory.memory) < BATCH_SIZE:
            return;
            
        transitions = self.replay_memory.sample(BATCH_SIZE)
        
        batch = Transition(*zip(*transitions))
                        
        states = torch.cat(batch.state)
        actions = torch.cat(batch.action)
        rewards = torch.cat(batch.reward)
        next_states = torch.cat(batch.next_state)
        dones = torch.cat(batch.done)
        
            
        # Compute Q(s_t, a) - the model computes Q(s_t), then we select the
        # columns of actions taken. These are the actions which would've been taken
        # for each batch state according to policy_net
        Q_expected = self.q_local(states).gather(1, actions) ## current    

        Q_targets_next = self.q_target(next_states).detach().max(1)[0] ## .unsqueeze(1)

        # Compute the expected Q values
        Q_targets = rewards + (gamma * Q_targets_next * (1-dones))
        
        self.q_local.train(mode=True)        
        self.optim.zero_grad()
        loss = self.mse_loss(Q_expected, Q_targets.unsqueeze(1))
        # backpropagation of loss to NN        
        loss.backward()
        self.optim.step()
       
        #for param in self.q_local.parameters():
        #   param.grad.data.clamp_(-1, 1)
        
        
        # ----------------------- update target networks ----------------------- #
        #self.soft_update(self.q_local, self.q_target, TAU)
        
        
    def soft_update(self, local_model, target_model, tau):
        """ tau (float): interpolation parameter"""
        
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau*local_param.data + (1.0-tau)*target_param.data)     
            
    def hard_update(self, local, target):
        for target_param, param in zip(target.parameters(), local.parameters()):
            target_param.data.copy_(param.data)            
            

