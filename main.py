import math
import networkx as nx
import streamlit as st
from campus_data import NAV_NODES, NAV_EDGES, ROOMS, get_destinations


def build_graph():
    G = nx.Graph()
    for name, pos in NAV_NODES.items():
        G.add_node(name, pos=pos)
    for a, b in NAV_EDGES:
        pa, pb = NAV_NODES[a], NAV_NODES[b]
        G.add_edge(a, b, weight=math.hypot(pa[0]-pb[0], pa[1]-pb[1]))
    return G


def find_path(graph, start, end):
    if start == end:
        return [start]
    def h(a, b):
        pa, pb = NAV_NODES[a], NAV_NODES[b]
        return math.hypot(pa[0]-pb[0], pa[1]-pb[1])
    try:
        return nx.astar_path(graph, start, end, heuristic=h, weight="weight")
    except nx.NetworkXNoPath:
        return None


def nearest_room(pos):
    best, best_d = None, 999999
    for name, info in ROOMS.items():
        x0, y0, x1, y1 = info["bounds"]
        cx, cy = (x0+x1)/2, (y0+y1)/2
        d = math.hypot(pos[0]-cx, pos[1]-cy)
        if d < best_d:
            best_d = d
            best = name
    return best


def find_checkpoint(path):
    mid_pos = NAV_NODES[path[len(path)//2]]
    return nearest_room(mid_pos)


def generate_directions(path):
    lines = []

    if len(path) < 2:
        lines.append(f"You're already at {path[0]}!")
        return lines

    angles = []
    for i in range(len(path)-1):
        p1, p2 = NAV_NODES[path[i]], NAV_NODES[path[i+1]]
        angles.append(math.atan2(p2[1]-p1[1], p2[0]-p1[0]))

    checkpoint = find_checkpoint(path)
    mid_idx = len(path) // 2
    checkpoint_shown = False
    passed = []

    # Determine which nodes are rooms vs hallway junctions
    def is_room(node):
        return not node.startswith("_")

    lines.append(f"Start at: {path[0]}")

    # Special case: only 2 or 3 nodes (very short path, usually across hall)
    if len(path) <= 3 and is_room(path[0]) and is_room(path[-1]):
        if len(path) == 2:
            lines.append(f"{path[-1]} is right next to you")
        else:
            # 3 nodes: room -> hallway -> room (across the hall)
            lines.append(f"Exit into the hallway — {path[-1]} is across the hall")
        lines.append(f"Arrive at: {path[-1]}")
        return lines

    # For longer paths, generate step-by-step directions
    # Skip the first segment (exiting starting room into hallway)
    started = False
    for i in range(len(path)):
        node = path[i]

        # Track named rooms we pass (not start/end, not hallway nodes)
        if is_room(node) and 0 < i < len(path)-1:
            passed.append(node)

        # Show checkpoint at midpoint for long paths
        if i >= mid_idx and not checkpoint_shown and len(path) > 4:
            checkpoint_shown = True
            if passed:
                lines.append(f"Walk past {', '.join(passed)}")
                passed = []
            lines.append(f">> Checkpoint: you should see {checkpoint} nearby")

        if i < len(angles)-1:
            diff = angles[i+1] - angles[i]
            while diff > math.pi: diff -= 2*math.pi
            while diff < -math.pi: diff += 2*math.pi

            is_turn = abs(diff) > 0.4

            # First segment: exiting the starting room
            if i == 0 and is_room(path[0]) and is_turn:
                # Determine which direction to head after exiting
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

            # Last segment: arriving at the destination room
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

            # Middle segments: hallway turns
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

    if passed:
        lines.append(f"Walk past {', '.join(passed)}")

    lines.append(f"Arrive at: {path[-1]}")
    return lines



# --- Streamlit App ---

st.title("IA East / TCT Campus Navigator")

graph = build_graph()
destinations = get_destinations()

start = st.selectbox("Where are you?", ["-- Select --"] + destinations)
end = st.selectbox("Where do you need to go?", ["-- Select --"] + destinations)

if start == "-- Select --" or end == "-- Select --":
    st.info("Select a starting location and a destination to get directions.")
else:
    path = find_path(graph, start, end)

    if path is None:
        st.error("No path found between those locations.")
    else:
        st.subheader(f"{start}  →  {end}")
        directions = generate_directions(path)
        for line in directions:
            st.write(line)

st.markdown("---")

st.image("floor plan.png", caption="Floor Plan Reference")
