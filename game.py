import argparse
import typing

# remove one or two marbles
# max node is first player
#

class Bag:
    """
    class representing marbles in a node

    """

    def __init__(self, red_marbles: int, blue_marbles: int) -> None:
        self.red_marbles = red_marbles
        self.blue_marbles = blue_marbles


class Node:
    def __init__(self, value: typing.Optional[int], bag: Bag, is_max, min: int, max: int) -> None:
        self.value = value # min-max value of the node
        self.max = max
        self.min = min
        self.is_max = is_max
        self.bag = bag  # Use passed bag directly
        self.children = []  # List to hold child nodes

    def __repr__(self) -> str:
        return f"Node(value={self.value}, bag=({self.bag.red_marbles}, {self.bag.blue_marbles}), is_max={self.is_max})"


class GameState:
    def __init__(self, current_turn: str, num_red: int, num_blue: int, version: str, first_player: str, depth: int) -> None:
        """
        current_turn:
            human for human
            computer for bot

        """
        self.current_turn = current_turn
        self.num_red = num_red
        self.num_blue = num_blue
        self.version = version
        self.first_player = first_player
        self.depth = depth


class MinMaxTree:
    def __init__(self, root: Node, game_state: GameState) -> None:
        self.root = root
        self.game_state = game_state

    def generate_mermaid_diagram(self):
        """
        Generate mermaid diagram to view tree structure using bfs
        Using bfs for visualization to avoid deep recursion, and this is just for debug :D
        """
        with open("mermaid_diagram.mmd", "w") as f:
            f.write("graph TD\n")
            queue = [self.root]  # Using a queue for BFS
            visited = set()  # Track visited nodes to avoid duplicates

            while queue:
                node = queue.pop(0)  # Get next node from queue
                if id(node) not in visited:
                    visited.add(id(node))

                    # Write node information
                    f.write(f"    {id(node)}[\"R:{node.bag.red_marbles} B:{node.bag.blue_marbles} "
                        f"{'MAX' if node.is_max else 'MIN'} {node.value}\"]\n")

                    # Process children
                    for child in node.children:
                        f.write(f"    {id(node)} --> {id(child)}\n")
                        queue.append(child)  # Add child to queue
    def debug(self):
        c = [self.root]
        while c:
            n = c.pop()
            print(f"Node: {n.value}, Bag: ({n.bag.red_marbles}, {n.bag.blue_marbles}), Is Max: {n.is_max}")
            c.extend(n.children)

    def generate_successors(self, node: Node) -> typing.List[Node]:
        successors = []

        if node.bag.red_marbles == 0 and node.bag.blue_marbles == 0:
            return successors

        # Determine move ordering based on game version
        if self.game_state.version == "standard":
            move_order = [
                ("red", 2),
                ("blue", 2),
                ("red", 1),
                ("blue", 1),
            ]
        else:  # misère version
            move_order = [
                ("blue", 1),
                ("red", 1),
                ("blue", 2),
                ("red", 2),
            ]

        # Generate successors based on the move order
        for color, count in move_order:
            if color == "red" and node.bag.red_marbles >= count:
                new_bag = Bag(node.bag.red_marbles - count, node.bag.blue_marbles)
                successors.append(Node(None, new_bag, not node.is_max, node.min, node.max))
            elif color == "blue" and node.bag.blue_marbles >= count:
                new_bag = Bag(node.bag.red_marbles, node.bag.blue_marbles - count)
                successors.append(Node(None, new_bag, not node.is_max, node.min, node.max))

        return successors

    def generate_tree(self, game_state: GameState) -> Node:
        """
        Notes:
        For each iteration of the game loop, we generate a full tree and calculate alpha beta pruning values,
        then we return the best move for the current player if they are the computer.
        We kinda do this every time it's the computer's turn, assuming that the previous best move is the root, with fresh values.

        Humans need to make their own choice, but it must be valid, can only remove 1 or 2 balls (if possible).
        """
        version = game_state.version
        def build_tree(node: Node, current_depth: int) -> None:
            if current_depth >= game_state.depth:
                node.value = self.evaluate_position(node, version)
                return

            successors = self.generate_successors(node)
            node.children = successors


            for child in successors:
                build_tree(child, current_depth + 1)

            # After building subtrees, calculate min/max value
            node.value = self.alpha_beta_calc(node, float('-inf'), float('inf'), game_state.depth - current_depth)
            #print(f"Building tree at depth {current_depth}, Value: {node.value}, Bag: ({node.bag.red_marbles}, {node.bag.blue_marbles}), Is Max: {node.is_max}")

        build_tree(self.root, 0)
        return self.root  # Return the root node after building the tree

    def evaluate_position(self, node: Node, version: str) -> int:
        if node.bag.red_marbles == 0 or node.bag.blue_marbles == 0:
            score = (node.bag.red_marbles * 2) + (node.bag.blue_marbles * 3)

            if version == "standard":
                return -score if node.is_max else score
            else:
                # misere selection is flipped
                return score if node.is_max else -score
        if not node.children: #terminal state
            return (node.bag.red_marbles * 2) + (node.bag.blue_marbles * 3)

        if node.is_max:
            return max(self.evaluate_position(child, version) for child in node.children)
        else:
            return min(self.evaluate_position(child, version) for child in node.children)

    def alpha_beta_calc(self, node: Node, alpha: int, beta: int, depth: int) -> int:
        """
        Perform alpha-beta pruning on the tree to find the optimal move for the computer.
        """
        if depth == 0 or not node.children:
            return self.evaluate_position(node, self.game_state.version)

        if node.is_max:
            value = float('-inf')
            for child in node.children:
                value = max(value, self.alpha_beta_calc(child, alpha, beta, depth - 1))
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            node.value = value
            return value
        else:
            value = float('inf')
            for child in node.children:
                value = min(value, self.alpha_beta_calc(child, alpha, beta, depth - 1))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            node.value = value
            return value

def check_game_over(game_state: GameState) -> bool:
    """
    Check if the game is over based on the current state.
    """
    return game_state.num_red == 0 or game_state.num_blue == 0

def calculate_score(red: int, blue: int) -> int:
    return (red * 2) + (blue * 3)

if __name__ == "__main__":
    args = argparse.ArgumentParser(description="red blue nim")
    # red_blue_nim.py <num-red> <num-blue> <version> <first-player> <depth>
    args.add_argument("num_red", type=int, help="number of red stones")
    args.add_argument("num_blue", type=int, help="number of blue stones")
    args.add_argument("version", type=str, help="version of the game") # misere, standard
    args.add_argument("first_player", type=str, help="who plays first")
    args.add_argument("depth", type=int, help="depth of the game tree")

    args = args.parse_args()

    # Create a GameState object with the provided arguments
    game_state = GameState(args.first_player, args.num_red, args.num_blue, args.version, args.first_player, args.depth)

    # Initialize the root node of the MinMax tree
    game_ended = check_game_over(game_state)
    while not game_ended:
        # annoyingly long game loop logic
        print("Current bag: "f"({game_state.num_red}, {game_state.num_blue})")
        if game_state.current_turn == 'computer':
            # Generate the tree and find the best move for the computer
            min_max_tree = MinMaxTree(Node(-1, Bag(game_state.num_red, game_state.num_blue), True, -999999, 999999), game_state)
            root = min_max_tree.generate_tree(game_state)
            best_move = max(root.children, key=lambda x: x.value)
            print(f"Computer removed from bag: ({best_move.bag.red_marbles}, {best_move.bag.blue_marbles})")
            game_state.num_red = best_move.bag.red_marbles
            game_state.num_blue = best_move.bag.blue_marbles
            game_state.current_turn = 'human'

        else:
            move = input("Enter your move (remove 1 or 2 marbles, format: <num>(R/B)): ").strip().upper()
            if move.endswith('R'):
                num_to_remove = int(move[:-1])
                if num_to_remove in [1, 2] and num_to_remove <= game_state.num_red:
                    game_state.num_red -= num_to_remove
                else:
                    print("Invalid move. You can only remove 1 or 2 red marbles, and there must be enough red marbles.")
                    continue
            elif move.endswith('B'):
                num_to_remove = int(move[:-1])
                if num_to_remove in [1, 2] and num_to_remove <= game_state.num_blue:
                    game_state.num_blue -= num_to_remove
                else:
                    print("Invalid move. You can only remove 1 or 2 blue marbles, and there must be enough blue marbles.")
                    continue
            else:
                print("Invalid input format. Please use <num>(R/B).")
                continue
            game_state.current_turn = 'computer'

        game_ended = check_game_over(game_state)

    # Game is over - announce winner
    final_score = calculate_score(game_state.num_red, game_state.num_blue)
    winner = 'human' if game_state.current_turn == 'computer' else 'computer'

    if game_state.version == 'standard':
        winner = 'computer' if game_state.current_turn == 'computer' else 'human'

    print(f"\nGame Over!")
    print(f"Winner: {winner.upper()}")
    print(f"Final Score: {final_score}")
