from graphviz import Digraph

"""
http://magjac.com/graphviz-visual-editor/?dot=digraph%20G%20%7B%0A%20%20node%20%5Bshape%3Dcircle%5D%0A%20%20a%20-%3E%20b0%0A%20%20xb%20%5Blabel%3D%22%22%2Cwidth%3D.1%2Cstyle%3Dinvis%5D%0A%20%20a%20-%3E%20xb%20%5Bstyle%3Dinvis%5D%0A%20%20b1%20%5Bwidth%3D.1%2Cstyle%3Dinvis%5D%0A%20%20a%20-%3E%20b1%20%5Bstyle%3Dinvis%5D%0A%20%20%7Brank%3Dsame%20b0%20-%3E%20xb%20-%3E%20b1%20%5Bstyle%3Dinvis%5D%7D%0A%20%20b0%20-%3E%20c0%0A%20%20xc%20%5Blabel%3D%22%22%2Cwidth%3D.1%2Cstyle%3Dinvis%5D%0A%20%20b0%20-%3E%20xc%20%5Bstyle%3Dinvis%5D%0A%20%20b0%20-%3E%20c1%0A%20%20%7Brank%3Dsame%20c0%20-%3E%20xc%20-%3E%20c1%20%5Bstyle%3Dinvis%5D%7D%0A%7D
"""
def visualize_binary_tree(tree):
    def add_nodes_edges(tree, dot=None):
        # Create Digraph object
        if dot is None:
            dot = Digraph(node_attr={'shape': 'circle'})
            dot.node(name=hex(id(tree)), label=str(tree.val))
        if not tree.left and not tree.right:
            return dot

        # Add nodes
        if tree.left:
            dot.node(name=hex(id(tree.left)), label=str(tree.left.val))
            dot.edge(hex(id(tree)), hex(id(tree.left)))
            dot = add_nodes_edges(tree.left, dot=dot)
        else:
            # invisl, let the generated binary tree can distinguish around the tree
            dot.node(name=hex(id(tree))+'invis_l', label='', style='invis', width='.1')
            dot.edge(hex(id(tree)), hex(id(tree))+'invis_l', style='invis')

        dot.node(name=hex(id(tree))+'invis_m', label='', style='invis', width='.1')
        dot.edge(hex(id(tree)), hex(id(tree))+'invis_m', style='invis')

        if tree.right:
            dot.node(name=hex(id(tree.right)), label=str(tree.right.val))
            dot.edge(hex(id(tree)), hex(id(tree.right)))
            dot = add_nodes_edges(tree.right, dot=dot)
        else:
            # invisl, let the generated binary tree can distinguish around the tree
            dot.node(name=hex(id(tree))+'invis_r', label='', style='invis', width='.1')
            dot.edge(hex(id(tree)), hex(id(tree))+'invis_r', style='invis')

        return dot

    # Add nodes recursively and create a list of edges
    dot = add_nodes_edges(tree)

    # Visualize the graph
    display(dot)
