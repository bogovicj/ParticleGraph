import torch
import torch_geometric as pyg
import torch_geometric.utils as pyg_utils
from ParticleGraph.utils import to_numpy


class PDE_E(pyg.nn.MessagePassing):
    """Interaction Network as proposed in this paper:
    https://proceedings.neurips.cc/paper/2016/hash/3147da8ab4a0437c15ef51a5cc7f2dc4-Abstract.html"""

    """
    Compute the acceleration of charged particles as a function of their relative position according to the Coulomb law.

    Inputs
    ----------
    data : a torch_geometric.data object

    Returns
    -------
    pred : float
        the acceleration of the particles (dimension 2)
    """

    def __init__(self, aggr_type=[], p=[], delta_t=[], clamp=[], pred_limit=[], prediction=[], bc_diff=[]):
        super(PDE_E, self).__init__(aggr='add')  # "mean" aggregation.

        self.p = p
        self.delta_t = delta_t
        self.clamp = clamp
        self.pred_limit = pred_limit
        self.prediction = prediction
        self.bc_diff = bc_diff

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        edge_index, _ = pyg_utils.remove_self_loops(edge_index)

        charge = self.p[to_numpy(x[:, 5])]

        acc = self.propagate(edge_index, x=x[:,1:3], charge=charge[:, None])
        return acc

    def message(self, x_i, x_j, charge_i, charge_j):
        r = torch.sqrt(torch.sum(self.bc_diff(x_j - x_i) ** 2, axis=1))
        distance_ij = torch.concatenate((r[:, None], r[:, None]), -1)
        direction_ij = self.bc_diff(x_j - x_i) / distance_ij

        charge_i = torch.concatenate((charge_i, charge_i), -1)
        charge_j = torch.concatenate((charge_j, charge_j), -1)
        acc = charge_i * charge_j * direction_ij / (distance_ij ** 2)

        return acc

    def psi(self, r, p1, p2):
        acc = p1 * p2 / r ** 2
        return -acc  # Elec particles
