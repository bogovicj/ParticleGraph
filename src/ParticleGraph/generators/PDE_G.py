import torch
import torch_geometric as pyg
import torch_geometric.utils as pyg_utils
from ParticleGraph.utils import to_numpy
import matplotlib.pyplot as plt


class PDE_G(pyg.nn.MessagePassing):
    """Interaction Network as proposed in this paper:
    https://proceedings.neurips.cc/paper/2016/hash/3147da8ab4a0437c15ef51a5cc7f2dc4-Abstract.html"""

    """
    Compute the acceleration of particles as a function of their relative position according to the gravity law.

    Inputs
    ----------
    data : a torch_geometric.data object

    Returns
    -------
    pred : float
        the acceleration of the particles (dimension 2)
    """

    def __init__(self, aggr_type=[], p=[], delta_t=[], clamp=[], pred_limit=[], bc_diff=[]):
        super(PDE_G, self).__init__(aggr='add')  # "mean" aggregation.

        self.p = p
        self.delta_t = delta_t
        self.clamp = clamp
        self.pred_limit = pred_limit
        self.bc_diff = bc_diff

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        edge_index, _ = pyg_utils.remove_self_loops(edge_index)

        mass = self.p[to_numpy(x[:, 5])]

        acc = self.propagate(edge_index, pos=x[:,1:3], mass=mass[:,None])
        return acc

    def message(self, pos_i, pos_j, mass_j):
        r = torch.sqrt(torch.sum(self.bc_diff(pos_j - pos_i) ** 2, axis=1))
        r = torch.clamp(r, min=self.clamp)
        distance_ij = torch.concatenate((r[:, None], r[:, None]), -1)

        direction_ij = self.bc_diff(pos_j - pos_i) / distance_ij
        mass = torch.concatenate((mass_j, mass_j), -1)
        
        acc = mass * direction_ij / (distance_ij ** 2)

        return torch.clamp(acc, max=self.pred_limit)

    def psi(self, r, p):
        r_ = torch.clamp(r, min=self.clamp)
        psi = p * r / r_ ** 3
        psi = torch.clamp(psi, max=self.pred_limit)

        return psi[:, None]
