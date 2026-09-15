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

    lines.append(f"Start at: {path[0]}")

    for i in range(len(path)):
        node = path[i]

        if not node.startswith("_") and 0 < i < len(path)-1:
            passed.append(node)

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

            if abs(diff) > 0.4:
                if passed:
                    lines.append(f"Walk past {', '.join(passed)}")
                    passed = []

                turn = "Turn left" if diff > 0 else "Turn right"
                near = nearest_room(NAV_NODES[path[i+1]])
                if near and near not in (path[0], path[-1]):
                    lines.append(f"{turn} (near {near})")
                else:
                    lines.append(f"{turn}")

    if passed:
        lines.append(f"Walk past {', '.join(passed)}")

    lines.append(f"Arrive at: {path[-1]}")
    return lines


# --- Streamlit App ---

st.title("IA East / TCT Campus Navigator")

st.image("floor plan.png", caption="Floor Plan Reference")

graph = build_graph()
destinations = get_destinations()

# Organize the catalog for display in an expander
entrances = sorted([d for d in destinations if "Entrance" in d])
rooms = sorted([d for d in destinations if d.startswith("Room ")],
               key=lambda r: int(r.split()[1]))
facilities = sorted([d for d in destinations
                     if d not in entrances and d not in rooms])

with st.expander("View All Destinations"):
    st.write("**Entrances:** " + ", ".join(entrances))
    st.write("**Rooms:** " + ", ".join(rooms))
    st.write("**Facilities:** " + ", ".join(facilities))

st.markdown("---")

start = st.selectbox("Where are you?", ["-- Select --"] + destinations)
end = st.selectbox("Where do you need to go?", ["-- Select --"] + destinations)

if start == "-- Select --" or end == "-- Select --":
    st.info("Select a starting location and a destination to get directions.")
    st.stop()

path = find_path(graph, start, end)

if path is None:
    st.error("No path found between those locations.")
else:
    st.subheader(f"{start}  →  {end}")
    directions = generate_directions(path)
    for line in directions:
        st.write(line)
