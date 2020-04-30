from glob import glob
import os
import json

MAPS_DIR = '.'

# some selector indeces to make the code more readable
NODE_NAME = 0
NODE_TYPE = 1

# region types
COAST = 'coast'
LAND = 'land'
SEA = 'sea'

# unit types
ARMY = 'army'
FLEET = 'fleet'

def get_map_dict(map_name):
    map_path = os.path.join(MAPS_DIR, map_name)
    nodes_path = os.path.join(map_path, 'nodes.json')
    edges_path = os.path.join(map_path, 'edges.json')
    positions_path = os.path.join(map_path, 'positions.json')

    nodes = json.load(open(nodes_path))
    edges = json.load(open(edges_path))
    positions = json.load(open(positions_path))

    map_dict = {
        'nodes': nodes,
        'edges': {
            'fleet': _get_fleet_edges(nodes, edges),
            'army': _get_army_edges(nodes, edges),
            'convoy': _get_convoy_edges(nodes, edges, positions)
        },
        'positions': positions
    }

    # TODO: check that graph is valid

    return map_dict

def _get_fleet_edges(nodes, edges):
    fleet_edges = {}
    fleet_edges.update({k:v for k,v in edges.items() if nodes[k][NODE_TYPE] == SEA})
    fleet_edges.update({k:_filter_regions(nodes, v, [COAST, SEA]) \
                            for k,v in edges.items() if nodes[k][NODE_TYPE] == COAST})
    return fleet_edges

def _get_army_edges(nodes, edges):
    army_edges = {k:_filter_regions(nodes, v, [LAND, COAST]) for k,v in edges.items() \
                            if nodes[k][NODE_TYPE] in [LAND, COAST]}
    return army_edges

def _get_convoy_edges(nodes, edges, positions):
    coasts = {k:v for k,v in nodes.items() if v[NODE_TYPE] == COAST}
    convoy_edges = {}

    def _set_sail(node, visited=[]):
        k, v = node[0], node[1]
        if v[NODE_TYPE] == COAST and k not in visited and len(visited) >= 2:
            if visited[0] not in convoy_edges.keys():
                convoy_edges.update({visited[0]:[(k,visited[1:])]})
            else:
                convoy_edges[visited[0]] += [(k,visited[1:])]
            return
        visited = visited + [k]
        adjacent_seas = set(_filter_regions(nodes, edges[k], [SEA])) - set(visited)
        adjacent_fleets = {r for r in adjacent_seas if _occupied_by(positions, r) == FLEET}
        if v[NODE_TYPE] == SEA:
            adjacent_coasts = set(_filter_regions(nodes, edges[k], [COAST])) - set(visited)
        else:
            adjacent_coasts = {}
        possible_moves = adjacent_fleets.union(adjacent_coasts)
        for r in possible_moves:
            _set_sail((r, nodes[r]), visited)

    for c in coasts.items():
        _set_sail(c)

    return convoy_edges

def _filter_regions(nodes, regions, by):
    return [r for r in regions if nodes[r][NODE_TYPE] in by]

def _occupied_by(positions, region):
    for player in positions.keys():
        for loc, unit in positions[player].items():
            if loc == region:
                return unit
