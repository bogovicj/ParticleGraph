import matplotlib
import matplotlib.pyplot as plt
# matplotlib.use("Qt5Agg")
import numpy as np
import torch
import umap
import vispy.scene
import vispy.plot as vp
import vispy.io as io
from matplotlib.ticker import FormatStrFormatter
from scipy.optimize import curve_fit
from vispy.scene import visuals
from ParticleGraph.fitting_models import linear_model
from ParticleGraph.models import Interaction_Particles, Interaction_Particle_Field, Signal_Propagation, Mesh_Laplacian, \
    Mesh_RPS
from ParticleGraph.utils import choose_boundary_values
from ParticleGraph.utils import to_numpy
from matplotlib import rc
import matplotlib as mpl

def get_embedding(model_a=None, dataset_number = 0):
    embedding = []
    embedding.append(model_a[dataset_number])
    embedding = to_numpy(torch.stack(embedding).squeeze())

    return embedding

def plot_training_particle_field(config, has_siren, has_siren_time, model_f, dataset_name, n_frames, model_name, log_dir, epoch, N, x, x_mesh, model_field, index_particles, n_particles, n_particle_types, model, n_nodes, n_node_types, index_nodes, dataset_num, ynorm, cmap, axis, device):

    simulation_config = config.simulation
    train_config = config.training
    model_config = config.graph_model

    max_radius = simulation_config.max_radius

    n_nodes = simulation_config.n_nodes
    n_nodes_per_axis = int(np.sqrt(n_nodes))

    fig = plt.figure(figsize=(12, 12))
    if axis:
        ax = fig.add_subplot(1, 1, 1)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        # plt.xlabel(r'$\ensuremath{\mathbf{a}}_{i0}$', fontsize=64)
        # plt.ylabel(r'$\ensuremath{\mathbf{a}}_{i1}$', fontsize=64)
        plt.xticks(fontsize=32.0)
        plt.yticks(fontsize=32.0)
    else:
        plt.axis('off')
    embedding = get_embedding(model.a, dataset_num)
    if n_particle_types > 1000:
        plt.scatter(embedding[:, 0], embedding[:, 1], c=to_numpy(x[:, 5]) / n_particles, s=5, cmap='viridis')
    else:
        for n in range(n_particle_types):
            plt.scatter(embedding[index_particles[n], 0],
                        embedding[index_particles[n], 1], color=cmap.color(n), s=200)  #

    plt.tight_layout()
    plt.savefig(f"./{log_dir}/tmp_training/embedding/particle/{model_name}_{dataset_name}_embedding_{epoch}_{N}.tif", dpi=170.7)
    plt.close()

    fig = plt.figure(figsize=(12, 12))
    if axis:
        ax = fig.add_subplot(1, 1, 1)
        # ax.xaxis.get_major_formatter()._usetex = False
        # ax.yaxis.get_major_formatter()._usetex = False
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
        ax.yaxis.set_major_locator(plt.MaxNLocator(3))
        # plt.xlabel(r'$d_{ij}$', fontsize=64)
        # plt.ylabel(r'$f(\ensuremath{\mathbf{a}}_i, d_{ij})$', fontsize=64)
        plt.xticks(fontsize=32)
        plt.yticks(fontsize=32)
        plt.xlim([0, simulation_config.max_radius])
        # plt.ylim([-0.15, 0.15])
        # plt.ylim([-0.04, 0.03])
        # plt.ylim([-0.1, 0.1])
        plt.tight_layout()
    rr = torch.tensor(np.linspace(0, simulation_config.max_radius, 200)).to(device)
    for n in range(n_particles):
        embedding_ = model.a[dataset_num, n, :] * torch.ones((200, model_config.embedding_dim), device=device)
        match model_config.particle_model_name:
            case 'PDE_ParticleField_A':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None], rr[:, None] / max_radius, embedding_), dim=1)
            case 'PDE_ParticleField_B':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         torch.abs(rr[:, None]) / max_radius, 0 * rr[:, None], 0 * rr[:, None],
                                         0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
        with torch.no_grad():
            func = model.lin_edge(in_features.float())
        func = func[:, 0]
        if n % 5 == 0:
            plt.plot(to_numpy(rr),
                     to_numpy(func * ynorm),
                     linewidth=8,
                     color=cmap.color(to_numpy(x[n, 5]).astype(int)), alpha=0.25)
    plt.ylim([-0.04, 0.03])
    plt.tight_layout()
    plt.savefig(f"./{log_dir}/tmp_training/embedding/function/{model_name}_{dataset_name}_function_{epoch}_{N}.tif", dpi=170.7)
    plt.close()

    fig = plt.figure(figsize=(12, 12))
    if has_siren:
        if has_siren_time:
            angle_list = [45, 135, 225, 315]
        else:
            angle_list = [0]

        for angle in angle_list:

            if has_siren_time:
                with torch.no_grad():
                    tmp = model_f(time=angle / n_frames) ** 2
            else:
                with torch.no_grad():
                    tmp = model_f() ** 2

            tmp = torch.reshape(tmp, (n_nodes_per_axis, n_nodes_per_axis))
            tmp = to_numpy(torch.sqrt(tmp))
            tmp = np.flipud(tmp)
            fig_ = plt.figure(figsize=(12, 12))
            axf = fig_.add_subplot(1, 1, 1)
            plt.imshow(tmp, cmap='grey', vmin=0, vmax=2)
            plt.xticks([])
            plt.yticks([])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/field/{model_name}_{epoch}_{N}_{angle}.tif", dpi=170.7)
            plt.close()

    else:
        im = to_numpy(model_field[dataset_num])
        im = np.reshape(im, (n_nodes_per_axis, n_nodes_per_axis))
        plt.imshow(im)
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f"./{log_dir}/tmp_training/embedding/field/{model_name}_{dataset_name}_field_{epoch}_{N}.tif", dpi=300)
        plt.close()

    # im = np.flipud(im)
    # io.imsave(f"./{log_dir}/tmp_training/embedding/field_pic_{dataset_name}_{epoch}_{N}.tif", im)

def plot_training (config, dataset_name, model_name, log_dir, epoch, N, x, index_particles, n_particles, n_particle_types, model, n_nodes, n_node_types, index_nodes, dataset_num, ynorm, cmap, axis, device):

    simulation_config = config.simulation
    train_config = config.training
    model_config = config.graph_model

    matplotlib.rcParams['savefig.pad_inches'] = 0

    if not('Mesh' in model_name):

        fig = plt.figure(figsize=(12, 12))
        if axis:
            plt.rcParams['text.usetex'] = True
            rc('font', **{'family': 'serif', 'serif': ['Palatino']})
            ax = fig.add_subplot(1,1,1)
            # ax.xaxis.get_major_formatter()._usetex = False
            # ax.yaxis.get_major_formatter()._usetex = False
            ax.xaxis.set_major_locator(plt.MaxNLocator(3))
            ax.yaxis.set_major_locator(plt.MaxNLocator(3))
            ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            plt.xlabel(r'$\ensuremath{\mathbf{a}}_{i0}$', fontsize=64)
            plt.ylabel(r'$\ensuremath{\mathbf{a}}_{i1}$', fontsize=64)
            plt.xticks(fontsize=32.0)
            plt.yticks(fontsize=32.0)
        else:
            plt.axis('off')

        embedding = get_embedding(model.a, dataset_num)
        embedding = embedding[n_nodes:,:]

        if n_particle_types > 1000:
            plt.scatter(embedding[:, 0], embedding[:, 1], c=to_numpy(x[:, 5])/n_particles, s=5, cmap='viridis')
        else:

            if  model_config.embedding_dim == 3:
                plt.close()
            # matplotlib.use("Qt5Agg")
                canvas = vispy.scene.SceneCanvas(show=False,  bgcolor='w',) # show=False) keys='interactive', show=True)
                view = canvas.central_widget.add_view()
                # generate data
                pos = embedding
                for n in range(n_particle_types):
                    scatter = visuals.Markers()
                    c =cmap.color(n)
                    scatter.set_data(pos[index_particles[n]], edge_width=0, face_color=c, size=10)
                    view.add(scatter)
                view.camera = 'turntable'  # or try 'arcball'
                try:
                    image = canvas.render()
                    io.write_png( f"./{log_dir}/tmp_training/embedding/particle/{model_name}_{dataset_name}_embedding_{epoch}_{N}.tif", image)
                    canvas.close()
                except:
                    print('Error in vispy')

            else:
                for n in range(n_particle_types):
                    plt.scatter(embedding[index_particles[n], 0],
                                embedding[index_particles[n], 1], color=cmap.color(n), s=200)

                plt.tight_layout()
                plt.savefig(f"./{log_dir}/tmp_training/embedding/particle/{model_name}_{dataset_name}_embedding_{epoch}_{N}.tif", dpi=170.7)
                plt.close()

    match model_name:

        case 'WaveMesh' | 'DiffMesh':
            rr = torch.tensor(np.linspace(-150, 150, 200)).to(device)
            popt_list = []
            for n in range(n_nodes):
                embedding_ = model.a[dataset_num, n, :] * torch.ones((200, 2), device=device)
                in_features = torch.cat((rr[:, None], embedding_), dim=1)
                h = model.lin_phi(in_features.float())
                h = h[:, 0]
                popt, pcov = curve_fit(linear_model, to_numpy(rr.squeeze()), to_numpy(h.squeeze()))
                popt_list.append(popt)
            t = np.array(popt_list)
            t = t[:, 0]
            fig = plt.figure(figsize=(8, 8))
            embedding = get_embedding(model.a, 1)
            plt.scatter(embedding[:, 0], embedding[:, 1], c=t[:, None], s=3, cmap='viridis')
            plt.xticks([])
            plt.yticks([])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/mesh_embedding_{dataset_name}_{epoch}_{N}.tif",dpi=300)
            plt.close()

            fig = plt.figure(figsize=(8, 8))
            t = np.reshape(t, (100, 100))
            plt.imshow(t, cmap='viridis')
            plt.xticks([])
            plt.yticks([])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/function/mesh_map_{dataset_name}_{epoch}_{N}.tif",
                        dpi=300)

            # fig = plt.figure(figsize=(8, 8))
            # t = np.array(popt_list)
            # t = t[:, 0]
            # pts = x[:, 1:3].detach().cpu().numpy()
            # tri = Delaunay(pts)
            # colors = np.sum(t[tri.simplices], axis=1)
            # plt.tripcolor(pts[:, 0], pts[:, 1], tri.simplices.copy(), facecolors=colors)
            # plt.xticks([])
            # plt.yticks([])
            # plt.tight_layout()
            # plt.savefig(f"./{log_dir}/tmp_training/embedding/mesh_Delaunay_{dataset_name}_{epoch}_{N}.tif",
            #             dpi=300)
            # plt.close()

        case 'PDE_GS':
            fig = plt.figure(figsize=(8, 4))
            ax = fig.add_subplot(1, 2, 1)
            rr = torch.tensor(np.logspace(7, 9, 1000)).to(device)
            for n in range(n_particles):
                embedding_ = model.a[1, n, :] * torch.ones((1000, model_config.embedding_dim), device=device)
                in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                         rr[:, None] / simulation_config.max_radius, 10 ** embedding_), dim=1)
                with torch.no_grad():
                    func = model.lin_edge(in_features.float())
                func = func[:, 0]
                plt.plot(to_numpy(rr), to_numpy(func) * to_numpy(ynorm),
                         color=cmap.color(to_numpy(x[n, 5]).astype(int)), linewidth=1)
            plt.xlabel('Distance [a.u]', fontsize=14)
            plt.ylabel('MLP [a.u]', fontsize=14)
            plt.xscale('log')
            plt.yscale('log')
            plt.tight_layout()
            ax = fig.add_subplot(1, 2, 2)
            plt.scatter(np.log(np.abs(to_numpy(y_batch[:, 0]))), np.log(np.abs(to_numpy(pred[:, 0]))), c='k', s=1,
                        alpha=0.15)
            plt.scatter(np.log(np.abs(to_numpy(y_batch[:, 1]))), np.log(np.abs(to_numpy(pred[:, 1]))), c='k', s=1,
                        alpha=0.15)
            plt.xlim([-10, 4])
            plt.ylim([-10, 4])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/function/func_{dataset_name}_{epoch}_{N}.tif", dpi=300)
            plt.close()

        case 'PDE_B':
            max_radius = 0.04
            fig = plt.figure(figsize=(12, 12))
            plt.rcParams['text.usetex'] = True
            rc('font', **{'family': 'serif', 'serif': ['Palatino']})
            ax = fig.add_subplot(1,1,1)
            rr = torch.tensor(np.linspace(-max_radius, max_radius, 1000)).to(device)
            func_list = []
            for n in range(n_particles):
                embedding_ = model.a[1, n, :] * torch.ones((1000, model_config.embedding_dim), device=device)
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         torch.abs(rr[:, None]) / max_radius, 0 * rr[:, None], 0 * rr[:, None],
                                         0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
                with torch.no_grad():
                    func = model.lin_edge(in_features.float())
                func = func[:, 0]
                func_list.append(func)
                if n % 5 == 0:
                    plt.plot(to_numpy(rr), to_numpy(func) * to_numpy(ynorm),
                             color=cmap.color(int(n // (n_particles / n_particle_types))), linewidth=4)
            plt.ylim([-1E-4, 1E-4])
            plt.xlabel(r'$x_j-x_i$', fontsize=64)
            plt.ylabel(r'$f_{ij}$', fontsize=64)
            # ax.xaxis.get_major_formatter()._usetex = False
            # ax.yaxis.get_major_formatter()._usetex = False
            ax.xaxis.set_major_locator(plt.MaxNLocator(3))
            ax.yaxis.set_major_locator(plt.MaxNLocator(5))
            ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            # ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
            fmt = lambda x, pos: '{:.1f}e-5'.format((x) * 1e5, pos)
            ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(fmt))
            plt.xticks(fontsize=32.0)
            plt.yticks(fontsize=32.0)
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/function/{model_name}_{dataset_name}_function_{epoch}_{N}.tif",dpi=170.7)
            plt.close()

        case 'PDE_G':
            fig = plt.figure(figsize=(12, 12))
            if axis:
                ax = fig.add_subplot(1, 1, 1)
                # ax.xaxis.get_major_formatter()._usetex = False
                # ax.yaxis.get_major_formatter()._usetex = False
                ax.xaxis.set_major_locator(plt.MaxNLocator(3))
                ax.yaxis.set_major_locator(plt.MaxNLocator(3))
                plt.xticks(fontsize=32)
                plt.yticks(fontsize=32)
                plt.xlim([0, simulation_config.max_radius])
                # plt.ylim([-0.15, 0.15])
                # plt.ylim([-0.04, 0.03])
                # plt.ylim([-0.1, 0.1])
                plt.tight_layout()
            rr = torch.tensor(np.linspace(simulation_config.min_radius, simulation_config.max_radius, 1000)).to(device)
            for n in range(n_particles):
                embedding_ = model.a[dataset_num, n, :] * torch.ones((1000, model_config.embedding_dim), device=device)
                in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                     rr[:, None] / simulation_config.max_radius, 0 * rr[:, None], 0 * rr[:, None],
                                     0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
                with torch.no_grad():
                    func = model.lin_edge(in_features.float())
                func = func[:, 0]
                plt.plot(to_numpy(rr),
                         to_numpy(func*ynorm),
                         linewidth=8,
                         color=cmap.color(to_numpy(x[n, 5]).astype(int)), alpha=0.25)
            plt.xlim([0, 0.02])
            plt.ylim([0, 0.5E6])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/function/{model_name}_{dataset_name}_function_{epoch}_{N}.tif", dpi=300)
            plt.close()

        case 'PDE_A'| 'PDE_A_bis' | 'PDE_ParticleField_A' | 'PDE_E' | 'PDE_B':
            fig = plt.figure(figsize=(12, 12))
            if axis:
                ax = fig.add_subplot(1, 1, 1)
                # ax.xaxis.get_major_formatter()._usetex = False
                # ax.yaxis.get_major_formatter()._usetex = False
                ax.xaxis.set_major_locator(plt.MaxNLocator(3))
                ax.yaxis.set_major_locator(plt.MaxNLocator(3))
                # plt.xlabel(r'$d_{ij}$', fontsize=64)
                # plt.ylabel(r'$f(\ensuremath{\mathbf{a}}_i, d_{ij})$', fontsize=64)
                plt.xticks(fontsize=32)
                plt.yticks(fontsize=32)
                plt.xlim([0, simulation_config.max_radius])
                # plt.ylim([-0.15, 0.15])
                # plt.ylim([-0.04, 0.03])
                # plt.ylim([-0.1, 0.1])
                plt.tight_layout()
            rr = torch.tensor(np.linspace(0, simulation_config.max_radius, 200)).to(device)
            for n in range(n_particles):
                embedding_ = model.a[dataset_num, n, :] * torch.ones((200, model_config.embedding_dim), device=device)
                if (model_config.particle_model_name == 'PDE_A'):
                    in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             rr[:, None] / simulation_config.max_radius, embedding_), dim=1)
                elif (model_config.particle_model_name == 'PDE_A_bis'):
                    in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             rr[:, None] / simulation_config.max_radius, embedding_, embedding_), dim=1)
                elif (model_config.particle_model_name == 'PDE_B'):
                    in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             0 * rr[:, None],
                                             0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
                elif model_config.particle_model_name == 'PDE_E':
                    in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             rr[:, None] / simulation_config.max_radius, embedding_, embedding_), dim=1)
                else:
                    in_features = torch.cat((rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             rr[:, None] / simulation_config.max_radius, 0 * rr[:, None],
                                             0 * rr[:, None],
                                             0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
                with torch.no_grad():
                    func = model.lin_edge(in_features.float())
                func = func[:, 0]
                if n % 5 == 0:
                    plt.plot(to_numpy(rr),
                             to_numpy(func*ynorm),
                             linewidth=8,
                             color=cmap.color(to_numpy(x[n, 5]).astype(int)), alpha=0.25)
                plt.ylim([-0.04, 0.03])
            plt.tight_layout()
            plt.savefig(f"./{log_dir}/tmp_training/embedding/function/{model_name}_{dataset_name}_function_{epoch}_{N}.tif", dpi=300)
            plt.close()

def analyze_edge_function(rr=None, vizualize=False, config=None, model_lin_edge=[], model_a=None, n_nodes=0, dataset_number = 0, n_particles=None, ynorm=None, types=None, cmap=None, dimension=2, device=None):
    func_list = []
    for n in range(n_particles):
        embedding_ = model_a[dataset_number, n_nodes+n, :] * torch.ones((1000, config.graph_model.embedding_dim), device=device)
        max_radius = config.simulation.max_radius
        match config.graph_model.particle_model_name:
            case 'PDE_A':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, embedding_), dim=1)
            case 'PDE_ParticleField_A':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, embedding_), dim=1)
            case 'PDE_A_bis':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, embedding_, embedding_), dim=1)
            case 'PDE_B':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, 0 * rr[:, None], 0 * rr[:, None],
                                         0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
            case 'PDE_ParticleField_B':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, 0 * rr[:, None], 0 * rr[:, None],
                                         0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
            case 'PDE_GS':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None], rr[:, None] / max_radius, 10**embedding_), dim=1)
            case 'PDE_G':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, 0 * rr[:, None],
                                         0 * rr[:, None],
                                         0 * rr[:, None], 0 * rr[:, None], embedding_), dim=1)
            case 'PDE_E':
                in_features = torch.cat((rr[:, None] / max_radius, 0 * rr[:, None],
                                         rr[:, None] / max_radius, embedding_, embedding_), dim=1)
        with torch.no_grad():
            func = model_lin_edge(in_features.float())
        func = func[:, 0]
        func_list.append(func)
        if ((n % 5 == 0) | (config.graph_model.particle_model_name=='PDE_GS')) & vizualize:
            plt.plot(to_numpy(rr),
                     to_numpy(func) * to_numpy(ynorm),
                     color=cmap.color(types[n].astype(int)), linewidth=8, alpha=0.25)
    func_list = torch.stack(func_list)
    coeff_norm = to_numpy(func_list)
    if coeff_norm.shape[0] > 1000:
        new_index = np.random.permutation(coeff_norm.shape[0])
        new_index = new_index[0:min(1000, coeff_norm.shape[0])]
        trans = umap.UMAP(n_neighbors=500, n_components=2, transform_queue_size=0).fit(coeff_norm[new_index])
        proj_interaction = trans.transform(coeff_norm)
    else:
        trans = umap.UMAP(n_neighbors=100, n_components=2, transform_queue_size=0).fit(coeff_norm)
        proj_interaction = trans.transform(coeff_norm)

    if vizualize:
        if config.graph_model.particle_model_name == 'PDE_GS':
            plt.xscale('log')
            plt.yscale('log')
        if config.graph_model.particle_model_name == 'PDE_G':
            plt.xscale('log')
            plt.yscale('log')
            plt.xlim([1E-3, 0.2])
        if config.graph_model.particle_model_name == 'PDE_E':
            plt.xlim([0, 0.05])
        plt.xlabel('Distance [a.u]', fontsize=12)
        plt.ylabel('MLP [a.u]', fontsize=12)

    return func_list, proj_interaction

def choose_training_model(model_config, device):
    
    aggr_type = model_config.graph_model.aggr_type
    n_particle_types = model_config.simulation.n_particle_types
    n_particles = model_config.simulation.n_particles
    dimension = model_config.simulation.dimension

    bc_pos, bc_dpos = choose_boundary_values(model_config.simulation.boundary)

    model=[]
    model_name = model_config.graph_model.particle_model_name
    match model_name:

        case 'PDE_ParticleField_A' | 'PDE_ParticleField_B':
            model = Interaction_Particle_Field(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos,
                                          dimension=dimension)
            model.edges = []
        case 'PDE_A' | 'PDE_A_bis' | 'PDE_B' | 'PDE_B_bis' | 'PDE_E' | 'PDE_G':
            model = Interaction_Particles(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos, dimension=dimension)
            model.edges = []
        case 'PDE_GS':
            model = Interaction_Particles(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos)
            t = np.arange(model_config.simulation.n_particles)
            t1 = np.repeat(t, model_config.simulation.n_particles)
            t2 = np.tile(t, model_config.simulation.n_particles)
            e = np.stack((t1, t2), axis=0)
            model.edges = torch.tensor(e, dtype=torch.long, device=device)
    model_name = model_config.graph_model.mesh_model_name
    match model_name:
        case 'DiffMesh':
            model = Mesh_Laplacian(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos)
            model.edges = []
        case 'WaveMesh':
            model = Mesh_Laplacian(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos)
            model.edges = []
        case 'RD_RPS_Mesh':
            model = Mesh_RPS(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos)
            model.edges = []
    model_name = model_config.graph_model.signal_model_name
    match model_name:
        case 'PDE_N':
            model = Signal_Propagation(aggr_type=aggr_type, config=model_config, device=device, bc_dpos=bc_dpos)
            model.edges = []
  
    if model==[]:
        raise ValueError(f'Unknown model {model_name}')

    return model, bc_pos, bc_dpos

def constant_batch_size(batch_size):
    def get_batch_size(epoch):
        return batch_size

    return get_batch_size

def increasing_batch_size(batch_size):
    def get_batch_size(epoch):
        return 1 if epoch < 1 else batch_size

    return get_batch_size

def set_trainable_parameters(model, lr_embedding, lr):
    trainable_params = [param for _, param in model.named_parameters() if param.requires_grad]
    n_total_params = sum(p.numel() for p in trainable_params) + torch.numel(model.a)

    embedding = model.a
    optimizer = torch.optim.Adam([embedding], lr=lr_embedding)

    _, *parameters = trainable_params
    for parameter in parameters:
        optimizer.add_param_group({'params': parameter, 'lr': lr})

    return optimizer, n_total_params

def set_trainable_division_parameters(model, lr):
    trainable_params = [param for _, param in model.named_parameters() if param.requires_grad]
    n_total_params = sum(p.numel() for p in trainable_params) + torch.numel(model.t)

    embedding = model.t
    optimizer = torch.optim.Adam([embedding], lr=lr)

    _, *parameters = trainable_params
    for parameter in parameters:
        optimizer.add_param_group({'params': parameter, 'lr': lr})

    return optimizer, n_total_params






