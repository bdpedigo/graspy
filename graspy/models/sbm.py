from .base import BaseGraphEstimator, _calculate_p, _fit_weights, cartprod
from ..utils import import_graph, binarize
import itertools
import numpy as np
from ..simulations import sbm, sample_edges


class SBEstimator(BaseGraphEstimator):
    def __init__(self, fit_weights=False, fit_degrees=False, directed=True, loops=True):
        super().__init__(fit_weights=fit_weights, directed=directed, loops=loops)
        self.fit_degrees = fit_degrees

    def fit(self, graph, y=None):
        """
        graph : 
        y : block assignments
        """
        if y is None:
            # TODO:
            # _fit_block_assignments(graph)
            raise NotImplementedError("No a posteriori case yet")
            # would have to do some kind of GMM thingy here
            # vertex labels = ...
        else:
            self.y = y
            vertex_labels = y

        graph = import_graph(graph)
        self.n_verts = graph.shape[0]

        # at this point assume block assignments are known

        # iterate over the blocks and calculate p
        # TODO: need to do this part in such a way as to align the labels
        # with a way that we can plot/sample
        block_labels, block_inv, block_sizes = np.unique(
            vertex_labels, return_inverse=True, return_counts=True
        )
        # TODO: could sort everything by size here?

        self.block_sizes_ = block_sizes

        n_blocks = len(block_labels)
        block_inds = range(n_blocks)

        block_members = []
        for bs, bl in zip(block_sizes, block_labels):
            block_members = block_members + bs * [bl]

        # TODO:
        # this is indexed in the same way as the internal model (unique)
        # could use unique like here?
        self.block_members_ = np.array(block_members)

        block_vert_inds = []
        for i in block_inds:
            inds = np.where(block_inv == i)[0]
            block_vert_inds.append(inds)

        block_pairs = cartprod(block_inds, block_inds)
        block_p = np.zeros((n_blocks, n_blocks))

        for p in block_pairs:
            from_block = p[0]
            to_block = p[1]
            from_inds = block_vert_inds[from_block]
            to_inds = block_vert_inds[to_block]
            block = graph[from_inds, :][:, to_inds]
            p = _calculate_p(block)
            block_p[from_block, to_block] = p

        self.block_p_ = block_p

        # block_map = cartprod(block_members, block_members).T
        block_map = cartprod(block_inv, block_inv).T
        p_by_edge = block_p[block_map[0], block_map[1]]
        p_mat = p_by_edge.reshape(graph.shape)
        self.p_mat_ = p_mat

        if self.fit_degrees:
            out_degree = np.count_nonzero(graph, axis=1)
            in_degree = np.count_nonzero(graph, axis=0)
            degree_corrections = out_degree + in_degree
            degree_corrections = degree_corrections.astype(float)
            # inds = np.append(inds, [degree_corrections.size])
            for i in block_inds:
                block_degrees = degree_corrections[block_vert_inds[i]]
                degree_corrections[block_vert_inds[i]] = degree_corrections[
                    block_vert_inds[i]
                ] / np.mean(block_degrees)
                # norm = np.mean(
                #     np.outer(
                #         degree_corrections[block_vert_inds[i]],
                #         degree_corrections[block_vert_inds[i]],
                #     )
                # )
                # print(norm)

            self.degree_corrections_ = degree_corrections
            p_mat = p_mat * np.outer(degree_corrections, degree_corrections)
            p_mat[p_mat > 1] = 1
            self.p_mat_ = p_mat
        else:
            self.degree_corrections_ = None

        if self.fit_weights:
            # TODO: something
            raise NotImplementedError("no weighted case yet")
            # _fit_weights(graph)

        return self

    def sample(self):
        # graph = sbm(
        #     self.block_sizes_,
        #     self.block_p_,
        #     loops=self.loops,
        #     directed=self.directed,
        #     dc=self.degree_corrections_,
        # )
        graph = sample_edges(self.p_mat_, directed=self.directed, loops=self.loops)
        return graph

    def _n_parameters(self):
        n_parameters = 0
        n_parameters += self.block_p_.size  # elements in block p matrix
        n_parameters += self.block_sizes_.size
        if self.fit_degrees:
            n_parameters += self.n_verts  # one degree correction per vert is stored
            # TODO: more than this? becasue now the position of verts w/in block matters
        return n_parameters

    # def score(self, graph):
    #     return super().score(graph)

    # def score_samples(self, graph):
    #     """
    #     Compute the weighted log probabilities for each sample.
    #     """
    #     # for each edge
    #     # look up where you are in the sbm
    #     #   if dcsbm, look up where you are in the dcvector
    #     #   take the product of those for your indices
    #     # for each non edge, also neet to find 1 - p...

    #     # if we had the p matrix ....
    #     # this would be as simple as
    #     # where graph is the unweighted graph:
    #     # P.ravel() <dot> graph * (1 - P.ravel()) <dot> (1 - graph)
    #     bin_graph = binarize(graph)
    #     p_mat = self.p_mat_
    #     successes = np.multiply(p_mat, bin_graph)
    #     failures = np.multiply((1 - p_mat), (1 - bin_graph))
    #     likelihood = successes + failures
    #     return np.log(likelihood)

    # def score_samples(self, graph):
    #     """
    #     Compute the weighted log probabilities for each sample.
    #     """
    #     # for each edge
    #     # look up where you are in the sbm
    #     #   if dcsbm, look up where you are in the dcvector
    #     #   take the product of those for your indices
    #     # for each non edge, also neet to find 1 - p...

    #     # if we had the p matrix ....
    #     # this would be as simple as
    #     # where graph is the unweighted graph:
    #     # P.ravel() <dot> graph * (1 - P.ravel()) <dot> (1 - graph)

    # def score(self, graph):
    #     """
    #     Compute the per-sample average log-likelihood of the given data X.
    #     """
    #     return self.score_samples(graph).mean()

    # def bic(self, graph):
    #     """
    #     do bic
    #     """
    #     return 1

    # def calc_p_matrix(self):

