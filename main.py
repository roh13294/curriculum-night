# bringing in the stuff we need lol
import math
import networkx as nx
import streamlit as st
from campus_data import NAV_NODES, NAV_EDGES, ROOMS, get_destinations


# --- Aditya: Start ---

# this builds the whole map as a graph so we can find paths thru it
def build_graph():
    G = nx.Graph()
    # throw all the nodes (locations) onto the graph
    for name, pos in NAV_NODES.items():
        G.add_node(name, pos=pos)
    # connect them with edges and calculate distance between each pair
    for a, b in NAV_EDGES:
        pa, pb = NAV_NODES[a], NAV_NODES[b]
        G.add_edge(a, b, weight=math.hypot(pa[0]-pb[0], pa[1]-pb[1]))
    return G


# finds the shortest path between two spots using a* algorithm
def find_path(graph, start, end):
    # if ur already there then just return
    if start == end:
        return [start]
    # heuristic function - basically guesses how far away the goal is
    def h(a, b):
        pa, pb = NAV_NODES[a], NAV_NODES[b]
        return math.hypot(pa[0]-pb[0], pa[1]-pb[1])
    try:
        return nx.astar_path(graph, start, end, heuristic=h, weight="weight")
    except nx.NetworkXNoPath:
        # no way to get there
        return None


# figures out what room is closest to a given position
def nearest_room(pos):
    best, best_d = None, 999999
    # loop thru every room and see which center is closest
    for name, info in ROOMS.items():
        x0, y0, x1, y1 = info["bounds"]
        cx, cy = (x0+x1)/2, (y0+y1)/2
        d = math.hypot(pos[0]-cx, pos[1]-cy)
        if d < best_d:
            best_d = d
            best = name
    return best


# grabs a checkpoint near the middle of the path so u know ur on track
def find_checkpoint(path):
    mid_pos = NAV_NODES[path[len(path)//2]]
    return nearest_room(mid_pos)
# --- Aditya: End ---


# --- Charvith: Start ---

#turns a path into actual directions u can follow
def generate_directions(path):
    lines = []

    # if the path is just one node u literally dont need to move
    if len(path) < 2:
        lines.append(f"You're already at {path[0]}!")
        return lines

    # calculate the angle of each segment so we can figure out turns
    angles = []
    for i in range(len(path)-1):
        p1, p2 = NAV_NODES[path[i]], NAV_NODES[path[i+1]]
        angles.append(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))

    # set up checkpoint stuff and a list of rooms we walk past
    checkpoint = find_checkpoint(path)
    mid_idx = len(path) // 2
    checkpoint_shown = False
    passed = []
# --- Charvith: End ---

# --- Sahay: Start ---
    # checks if a node is an actual room or just a hallway junction
    def is_room(node):
        return not node.startswith("_")

    lines.append(f"Start at: {path[0]}")

    # if its a super short path (like across the hall) just say that
    if len(path) <= 3 and is_room(path[0]) and is_room(path[-1]):
        if len(path) == 2:
            lines.append(f"{path[-1]} is right next to you")
        else:
            lines.append(f"Exit into the hallway — {path[-1]} is across the hall")
        lines.append(f"Arrive at: {path[-1]}")
        return lines

    # ok for longer paths we gotta go step by step
    started = False
    for i in range(len(path)):
        node = path[i]
# --- Sahay: End ---

# --- Rohan: Start ---
        # keep track of rooms we pass by so we can mention them
        if is_room(node) and 0 < i < len(path)-1:
            passed.append(node)

        # drop a checkpoint halfway thru so u dont get lost
        if i >= mid_idx and not checkpoint_shown and len(path) > 4:
            checkpoint_shown = True
            if passed:
                lines.append(f"Walk past {', '.join(passed)}")
                passed = []
            lines.append(f">> Checkpoint: you should see {checkpoint} nearby")

        if i < len(angles)-1:
            # figure out if we need to turn by comparing angles
            diff = angles[i+1] - angles[i]
            while diff > math.pi: diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi

            is_turn = abs(diff) > 0.4

            # first step = leaving the room ur starting from
            if i == 0 and is_room(path[0]) and is_turn:
                # figure out which way to go when u walk out
                next_angle = angles[1] if len(angles) > 1 else angles[0]
                deg = math.degrees(next_angle)
                if -45 < deg < 45:
                    heading = "head right"
                elif 135 < deg or deg < -135:
                    heading = "head left"
                elif 45 <= deg <= 135:
                    heading = "continue down the hall"
                else:
                    heading = "continue down the hall"
                lines.append(f"Exit {path[0]} and {heading}")
                started = True
                continue

            # last step = ur basically there, tell them which side its on
            if i == len(angles)-1 and is_room(path[-1]) and is_turn:
                if passed:
                    lines.append(f"Walk past {', '.join(passed)}")
                    passed = []
                if diff > 0:
                    lines.append(f"{path[-1]} will be on your left")
                else:
                    lines.append(f"{path[-1]} will be on your right")
                lines.append(f"Arrive at: {path[-1]}")
                return lines

            # any other turn = a hallway turn, say whats nearby
            if is_turn:
                if passed:
                    lines.append(f"Walk past {', '.join(passed)}")
                    passed = []

                turn = "Turn left" if diff > 0 else "Turn right"
                near = nearest_room(NAV_NODES[path[i+1]])
                if near and near not in (path[0], path[-1]):
                    lines.append(f"{turn} at the hallway (near {near})")
                else:
                    lines.append(f"{turn} at the hallway")

    # if theres rooms left we havent mentioned yet
    if passed:
        lines.append(f"Walk past {', '.join(passed)}")

    lines.append(f"Arrive at: {path[-1]}")
    return lines
# --- Rohan: End ---



# --- Sid: Start ---

# sets up the whole streamlit page
st.title("IA East / TCT Campus Navigator")

# build the graph and get all the places u can go
graph = build_graph()
destinations = get_destinations()

# dropdown menus for picking start and end
start = st.selectbox("Where are you?", ["-- Select --"] + destinations)
end = st.selectbox("Where do you need to go?", ["-- Select --"] + destinations)

# if they havent picked both yet just show a lil message
if start == "-- Select --" or end == "-- Select --":
    st.info("Select a starting location and a destination to get directions.")
else:
    # find the path and show directions
    path = find_path(graph, start, end)

    if path is None:
        st.error("No path found between those locations.")
    else:
        st.subheader(f"{start}  →  {end}")
        directions = generate_directions(path)
        # print each step one by one
        for line in directions:
            st.write(line)

st.markdown("---")

# show the floor plan pic at the bottom for reference
st.image("floor plan.png", caption="Floor Plan Reference")
# --- Sid: End ---
