#%%
from graspy.models import EREstimator, SBEstimator, RDPGEstimator
from graspy.datasets import load_drosophila_left
from graspy.plot import heatmap
from graspy.utils import symmetrize, binarize
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

## Load data
sns.set_context("talk")
left_adj, cell_labels = load_drosophila_left(return_labels=True)
left_adj_uw = left_adj.copy()
left_adj_uw[left_adj_uw > 0] = 1

left_adj_uw = symmetrize(left_adj_uw, method="avg")
left_adj_uw = binarize(left_adj_uw)


def evaluate_models(
    graph, labels=None, title=None, plot_graphs=False, min_comp=0, max_comp=1, n_comp=5
):

    if plot_graphs:
        heatmap(graph, inner_hier_labels=cell_labels)

    ## Set up models to test
    non_rdpg_models = [
        EREstimator(fit_degrees=False),
        EREstimator(fit_degrees=True),
        SBEstimator(fit_degrees=False),
        SBEstimator(fit_degrees=True),
    ]

    d = [int(i) for i in np.logspace(min_comp, max_comp, n_comp)]
    rdpg_models = [RDPGEstimator(n_components=i) for i in d]
    models = non_rdpg_models + rdpg_models

    names_nonRDPG = ["ER", "DCER", "SBM", "DCSBM"]
    names_RDPG = ["RDPG {}".format(i) for i in d]
    names = names_nonRDPG + names_RDPG

    bics = []
    log_likelihoods = []

    ## Test models
    for model, name in zip(models, names):
        m = model.fit(graph, y=labels)
        if plot_graphs:
            heatmap(m.p_mat_, inner_hier_labels=labels, title=(name + "P matrix"))
            heatmap(m.sample(), inner_hier_labels=labels, title=(name + "sample"))
        bic = m.bic(graph)
        log_likelihoods.append(m.score(graph))
        bics.append(bic)
        plt.show()

    bics = np.array(bics)
    log_likelihoods = np.array(log_likelihoods)

    ## Plot results
    plt.figure()
    fig, ax = plt.subplots(1, 2, sharey=False, figsize=(10, 10))
    sns.pointplot(names_nonRDPG, bics[:4], join=False, ax=ax[0])
    sns.scatterplot(d, bics[4:])
    ax[1].set_xlabel("RDPG - d")
    ax[0].set_xlabel("A priori models")
    ax[0].set_ylabel("rBIC")
    plt.suptitle(title, y=0.94)

    plt.figure()
    fig, ax = plt.subplots(1, 2, sharey=False, figsize=(10, 10))
    sns.pointplot(names_nonRDPG, -log_likelihoods[:4], join=False, ax=ax[0])
    sns.scatterplot(d, -log_likelihoods[4:])
    ax[1].set_xlabel("RDPG - d")
    ax[0].set_xlabel("A priori models")
    ax[0].set_ylabel("-ln(Likelihood)")
    plt.suptitle(title, y=0.94)

    return bics, log_likelihoods


#%% Set up some simulations
from graspy.simulations import p_from_latent, sample_edges
from graspy.plot import pairplot

p_kwargs = {}
sample_kwargs = {}
n_verts = 1000
show_graphs = False
show_latent = True
names = []
graph_sims = []


def get_graph(latent):
    if type(latent) is tuple:
        left_latent = latent[0]
        right_latent = latent[1]
    else:
        left_latent = latent
        right_latent = None
    true_P = p_from_latent(left_latent, right_latent, **p_kwargs)
    graph = sample_edges(true_P, **sample_kwargs)
    if show_graphs:
        heatmap(graph)
    if show_latent:
        if right_latent is not None:
            labels = np.array(
                len(left_latent) * ["left"] + len(right_latent) * ["right"]
            )
            # print(left_latent.shape)
            # print(right_latent.shape)
            latent = np.concatenate((left_latent, right_latent), axis=0)
            pairplot(latent, labels=labels)
        else:
            pairplot(left_latent)
    return graph


# Single point in latent space
# this should be an ER model
latent = np.array(n_verts * [0.5])
latent = latent[:, np.newaxis]  # to make it n x d
graph = get_graph(latent)
names.append("Latent point")
graph_sims.append(graph)

# Line in 1d
# should be a degree corrected ER
latent = np.random.uniform(0.25, 0.75, n_verts)
latent = latent[:, np.newaxis]
graph = get_graph(latent)
names.append("Latent line - uniform")
graph_sims.append(graph)

# Line in 1d, but gaussian
latent = np.random.normal(0.5, 0.1, n_verts)
latent = latent[:, np.newaxis]
graph = get_graph(latent)
names.append("Latent line - gaussian")
graph_sims.append(graph)

# directed latent lines
left_latent = np.random.uniform(0.25, 0.75, n_verts)
left_latent = left_latent[:, np.newaxis]
right_latent = np.random.uniform(0.25, 0.75, n_verts)
right_latent = right_latent[:, np.newaxis]
latent = (left_latent, right_latent)
graph = get_graph(latent)
names.append("Directed latent lines - same uniform")
graph_sims.append(graph)

# directed latent lines, different uniform
left_latent = np.random.uniform(0.4, 0.8, n_verts)
left_latent = left_latent[:, np.newaxis]
right_latent = np.random.uniform(0.2, 0.5, n_verts)
right_latent = right_latent[:, np.newaxis]
latent = (left_latent, right_latent)
graph = get_graph(latent)
names.append("Directed latent lines - same uniform")
graph_sims.append(graph)

# directed latent lines, different gaussian
left_latent = np.random.normal(0.4, 0.1, n_verts)
left_latent = left_latent[:, np.newaxis]
right_latent = np.random.normal(0.8, 0.05, n_verts)
right_latent = right_latent[:, np.newaxis]
latent = (left_latent, right_latent)
graph = get_graph(latent)
names.append("Directed latent lines - same uniform")
graph_sims.append(graph)

# sbm simple, 2 block
point1 = [0.1, 0.6]
point2 = [0.6, 0.1]
points = np.array([point1, point2])
inds = np.array(int(n_verts / 2) * [0] + int(n_verts / 2) * [1])
latent = np.array(points[inds])
graph = get_graph(latent)
names.append("SBM - 2 block")
graph_sims.append(graph)


# dcsbm, 2 line, uniform
thetas = np.array([0 * np.pi, 0.5 * np.pi])
distances = np.random.uniform(0.2, 0.9, n_verts)
vec1 = np.array([np.cos(thetas[0]), np.sin(thetas[0])])
vec2 = np.array([np.cos(thetas[1]), np.sin(thetas[1])])
latent1 = np.multiply(distances[: int(n_verts / 2)][:, np.newaxis], vec1[np.newaxis, :])
latent2 = np.multiply(distances[int(n_verts / 2) :][:, np.newaxis], vec2[np.newaxis, :])
latent = np.concatenate((latent1, latent2), axis=0)
graph = get_graph(latent)
names.append("DCSBM - 2 line uniform")
graph_sims.append(graph)


# dcsbm, 2 line, beta
thetas = np.array([0.1 * np.pi, 0.4 * np.pi])
distances = np.random.beta(0.5, 0.5, n_verts)
vec1 = np.array([np.cos(thetas[0]), np.sin(thetas[0])])
vec2 = np.array([np.cos(thetas[1]), np.sin(thetas[1])])
latent1 = np.multiply(distances[: int(n_verts / 2)][:, np.newaxis], vec1[np.newaxis, :])
latent2 = np.multiply(distances[int(n_verts / 2) :][:, np.newaxis], vec2[np.newaxis, :])
latent = np.concatenate((latent1, latent2), axis=0)
graph = get_graph(latent)
names.append("DCSBM - 2 line beta")
graph_sims.append(graph)

inds = np.array(int(n_verts / 2) * [0] + int(n_verts / 2) * [1])
for graph, name in zip(graph_sims, names):
    evaluate_models(graph, inds, title=name)
