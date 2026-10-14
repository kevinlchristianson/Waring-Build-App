"""Waring Build: the floor plan as data.

Plan coordinates are feet. x runs east from the outside face of the west wall framing,
y runs north from the outside face of the front (south) wall framing. The front of the house
(porch, garage door) is assumed to face south, so the sheets read like the BuildWise plan:
front at the bottom, bedrooms on the left (west), garage on the right (east).

Walls are given by their centre lines. Exterior walls are 2x6 (5-1/2"), interior partitions 2x4 (3-1/2").
Source: BuildWise LLC plan 3933 (3 bed, 2 bath, 1,800 sq ft conditioned, 528 sq ft garage, 58' x 40').
"""

W, D = 58.0, 40.0                 # overall framing, west-east x south-north
T_EXT, T_INT = 5.5 / 12, 3.5 / 12
C = T_EXT / 2                     # exterior wall centre line, in from the outside face
CEIL = 9.0                        # flat ceiling throughout, garage included
PLATE_H = 9.0 + 1.125 / 12        # 104-5/8" precut studs + 3 plates
PITCH = 6 / 12                    # 6:12 simple gable, ridge east-west on the centre line
OVERHANG = 1.0
DOOR_H = 80 / 12                  # interior doors 6'-8"
HEAD = 8.0                        # window and exterior door heads

# ------------------------------------------------------------------ walls
# n, x1, y1, x2, y2 (centre line), type, note
#   E  exterior 2x6 @ 16" o.c., 7/16" OSB, house wrap, R-21 batts (bearing on the south and north walls)
#   P  interior 2x4 @ 16" o.c. partition (non-bearing: the roof trusses clear-span 40')
#   G  garage separation 2x4 @ 16", insulated, 1/2" gypsum on the garage side (IRC R302.6)
#   M  mechanical room in the garage, 2x4 @ 16", gypsum both sides
WALLS = [
    (1, 0, C, W, C, 'E', 'front (south) exterior wall; bears the roof trusses'),
    (2, W - C, 0, W - C, D, 'E', 'east exterior wall (gable end)'),
    (3, 0, D - C, W, D - C, 'E', 'rear (north) exterior wall; bears the roof trusses'),
    (4, C, 0, C, D, 'E', 'west exterior wall (gable end)'),
    (5, 12, C, 12, D - C, 'P', 'bedroom wing / great room'),
    (6, C, 12.5, 12, 12.5, 'P', 'Bedroom 3 / its closet and the hall'),
    (7, C, 15, 8, 15, 'P', 'Bedroom 3 closet / Bath 2'),
    (8, 8, 12.5, 8, 28, 'P', 'closets and Bath 2 / hall'),
    (9, C, 25.5, 8, 25.5, 'P', 'Bath 2 / Bedroom 2 closet'),
    (10, C, 28, 12, 28, 'P', 'Bedroom 2 / its closet and the hall'),
    (11, 28, C, 28, 10, 'P', 'living room / mud-laundry'),
    (12, 28, 10, 36, 10, 'P', 'mud-laundry / back hall'),
    (13, 36, C, 36, 24, 'G', 'house / garage'),
    (14, 34, 24, W - C, 24, 'G', 'primary suite / garage and back hall'),
    (15, 34, 24, 34, D - C, 'P', 'primary bedroom / kitchen and pantry'),
    (16, 48, 24, 48, D - C, 'P', 'primary bedroom / primary bath and WIC'),
    (17, 48, 34, W - C, 34, 'P', 'primary bath / WIC'),
    (18, 28, 35, 28, D - C, 'P', 'pantry / kitchen'),
    (19, 28, 35, 34, 35, 'P', 'pantry / kitchen'),
    (20, 52, 18, 52, 24, 'M', 'mechanical room / garage'),
    (21, 52, 18, W - C, 18, 'M', 'mechanical room / garage'),
]
THICK = {'E': T_EXT, 'P': T_INT, 'G': T_INT, 'M': T_INT}


def wall(n):
    return next(w for w in WALLS if w[0] == n)


def along_x(w):
    return abs(w[2] - w[4]) < 1e-6


# ------------------------------------------------------------------ doors and openings
# tag, wall, centre along the wall (x for an east-west wall, y for a north-south one), leaf width (ft),
# height (ft), kind, room it serves, hinge end ('lo' = west/south end), swing side ('+' = toward +y/+x), note
#   kind: swing | pair (two leaves) | bifold | overhead | cased (no door)
DOORS = [
    ('D1', 1, 25.0, 3.0, HEAD, 'swing', 'Front entry', 'hi', '+', 'insulated fiberglass, 3\'-0" x 8\'-0", lever and deadbolt; threshold flush with the porch'),
    ('D2', 3, 19.5, 6.0, HEAD, 'pair', 'Dining', 'lo', '-', 'French doors to the rear patio, 6\'-0" x 8\'-0" pair, one active leaf, low-E glass'),
    ('D3', 13, 21.0, 3.0, DOOR_H, 'swing', 'Back hall', 'hi', '-', 'house to garage: 20-minute rated, solid core, self-closing (IRC R302.5.1); 1-step down to the garage slab'),
    ('D4', 1, 47.0, 16.0, 8.0, 'overhead', 'Garage', 'lo', '+', '16\'-0" x 8\'-0" insulated overhead door with opener'),
    ('D5', 2, 9.0, 3.0, DOOR_H, 'swing', 'Garage', 'lo', '-', 'garage service door, steel, 3\'-0" x 6\'-8"'),
    ('D6', 6, 10.0, 2 + 8 / 12, DOOR_H, 'swing', 'Bedroom 3', 'hi', '-', ''),
    ('D7', 6, 4.2, 5.0, DOOR_H, 'bifold', 'Bedroom 3 closet', 'lo', '-', '2 pair of 2\'-6" bifolds'),
    ('D8', 8, 20.25, 2 + 8 / 12, DOOR_H, 'swing', 'Bath 2', 'lo', '-', 'privacy lock'),
    ('D9', 10, 4.2, 5.0, DOOR_H, 'bifold', 'Bedroom 2 closet', 'lo', '+', '2 pair of 2\'-6" bifolds'),
    ('D10', 10, 10.0, 2 + 8 / 12, DOOR_H, 'swing', 'Bedroom 2', 'hi', '+', ''),
    ('D11', 12, 30.25, 2 + 8 / 12, DOOR_H, 'swing', 'Mud / laundry', 'lo', '-', ''),
    ('D12', 15, 25.9, 2 + 8 / 12, DOOR_H, 'swing', 'Primary bedroom', 'lo', '+', ''),
    ('D13', 16, 25.9, 2 + 8 / 12, DOOR_H, 'swing', 'Primary bath', 'lo', '+', 'privacy lock'),
    ('D14', 17, 51.4, 2.5, DOOR_H, 'swing', 'WIC', 'lo', '+', ''),
    ('D15', 18, 37.4, 2.5, DOOR_H, 'swing', 'Pantry', 'lo', '+', ''),
    ('D16', 21, 54.5, 2 + 8 / 12, DOOR_H, 'swing', 'Mechanical room', 'lo', '-', 'swings out into the garage, clear of the water heater'),
    ('O1', 5, 19.5, 3.5, DOOR_H, 'cased', 'Hall', 'lo', '+', 'cased opening, hall to the great room'),
]

# ------------------------------------------------------------------ windows
# tag, wall, centre along the wall, width, height, sill, room, type
WINDOWS = [
    ('N1', 1, 6.0, 3.0, 5.0, 3.0, 'Bedroom 3', 'single hung, egress'),
    ('N2', 1, 14.0, 3.0, 5.0, 3.0, 'Living room', 'single hung'),
    ('N3', 1, 19.5, 3.0, 5.0, 3.0, 'Living room', 'single hung'),
    ('N4', 4, 10.1, 3.0, 5.0, 3.0, 'Bedroom 3', 'single hung, egress'),
    ('N5', 4, 21.0, 2.0, 3.0, 5.0, 'Bath 2', 'single hung, obscure glass'),
    ('N6', 4, 37.6, 3.0, 5.0, 3.0, 'Bedroom 2', 'single hung, egress'),
    ('N7', 3, 6.0, 3.0, 5.0, 3.0, 'Bedroom 2', 'single hung, egress'),
    ('N8', 3, 25.75, 3.0, 4.0, 4.0, 'Kitchen', 'single hung, over the rear counter'),
    ('N9', 3, 41.0, 3.0, 5.0, 3.0, 'Primary bedroom', 'single hung, egress'),
    ('N10', 2, 26.0, 2.0, 3.0, 5.0, 'Primary bath', 'single hung, obscure glass'),
    ('N11', 2, 14.0, 3.0, 4.0, 4.0, 'Garage', 'single hung'),
]

# ------------------------------------------------------------------ rooms
# name, x1, x2, y1, y2 on wall centre lines (0 / W / D mean the exterior wall), colour key, open edges
# colour keys follow the Zero Rd sheets: bed, wet, serv, circ, live, fixed
ROOMS = [
    ('Bedroom 3', 0, 12, 0, 12.5, 'bed', ''),
    ('Closet', 0, 8, 12.5, 15, 'serv', ''),
    ('Bath 2', 0, 8, 15, 25.5, 'wet', ''),
    ('Closet', 0, 8, 25.5, 28, 'serv', ''),
    ('Bedroom 2', 0, 12, 28, 40, 'bed', ''),
    ('Hall', 8, 12, 12.5, 28, 'circ', ''),
    ('Living Room', 12, 28, 0, 18, 'live', 'N'),
    ('Dining', 12, 23, 18, 40, 'live', 'SE'),
    ('Kitchen', 23, 34, 18, 40, 'live', 'SW'),
    ('Pantry', 28, 34, 35, 40, 'serv', ''),
    ('Mud / Laundry', 28, 36, 0, 10, 'wet', ''),
    ('Back Hall', 28, 36, 10, 18, 'circ', 'WN'),
    ('Back Hall', 34, 36, 18, 24, 'circ', 'W'),
    ('Primary Bedroom', 34, 48, 24, 40, 'bed', ''),
    ('Primary Bath', 48, 58, 24, 34, 'wet', ''),
    ('WIC', 48, 58, 34, 40, 'serv', ''),
    ('Garage', 36, 58, 0, 24, 'garage', ''),
    ('Mech Room', 52, 58, 18, 24, 'serv', ''),
]
OUTDOOR = [
    ('Front Porch', 12, 30, -6, 0, '6\' x 18\' concrete, under its own shed roof on 6x6 posts'),
    ('Rear Patio', 12.5, 26.5, 40, 50, '10\' x 14\' concrete, covered, on 6x6 posts'),
    ('Driveway', 37, 57, -14, 0, 'concrete apron to the garage door'),
]
# room name labels: (text, x, y, size)
LABELS = [
    ('Bedroom 3', 6.0, 10.6, 9), ('Closet', 4.2, 13.75, 7), ('Bath 2', 4.6, 23.4, 9), ('Closet', 4.2, 26.75, 7),
    ('Bedroom 2', 6.6, 29.6, 9), ('Hall', 10.0, 24.6, 8), ('Living Room', 16.0, 15.6, 10), ('Dining', 15.0, 37.0, 10),
    ('Kitchen', 30.7, 22.0, 10), ('Pantry', 31.0, 38.6, 8), ('Mud / Laundry', 31.2, 8.2, 9), ('Back Hall', 32.0, 15.0, 8),
    ('Primary Bedroom', 40.0, 37.6, 10), ('Primary Bath', 51.4, 33.0, 9), ('WIC', 55.5, 36.7, 9), ('Garage', 44.5, 21.4, 11),
    ('Mech Room', 55.0, 23.2, 8), ('Front Porch', 18.0, -3.0, 9), ('Rear Patio', 19.5, 47.5, 9),
]


def face(v, lo_side, axis):
    """the finished (stud) face of a room edge on the wall centre line v. lo_side: True when the room is on the + side."""
    top = W if axis == 'x' else D
    if v <= 0.01:
        return T_EXT
    if v >= top - 0.01:
        return top - T_EXT
    return v + (T_INT / 2 if lo_side else -T_INT / 2)


def clear(r):
    """a room's stud-face rectangle"""
    _, x1, x2, y1, y2 = r[:5]
    return face(x1, True, 'x'), face(x2, False, 'x'), face(y1, True, 'y'), face(y2, False, 'y')


# ------------------------------------------------------------------ fixtures and furniture
# kind, x1, x2, y1, y2, front (the side it faces: N S E W), label, note
# kinds the 3D draws: bed, nightstand, dresser, sofa, coffee, table, tv, island, counter, range, fridge,
# tub, toilet, vanity, shower, washer, dryer, linen, shelves, rods, bench, car, wh, panel, condenser, stair
F = T_EXT
FIXTURES = [
    # Bedroom 3: queen, headboard on the west wall
    ('bed', F, F + 6.67, 3.5, 8.5, 'E', 'Queen bed', ''),
    ('nightstand', F, F + 1.5, 1.8, 3.3, 'E', 'Nightstand', ''),
    ('nightstand', F, F + 1.5, 8.7, 10.2, 'E', 'Nightstand', ''),
    ('dresser', 9.0, 11.85, F, F + 1.5, 'N', 'Dresser', ''),
    # Bath 2: tub across the south wall, linen tower beside it, toilet on the west wall, vanity on the north wall
    ('tub', 2.854, 7.854, 15.146, 17.646, 'N', 'Tub / shower', '60" x 30" alcove tub with shower, tile surround; drain and valve at the east end, on wall 8'),
    ('linen', F, 2.704, 15.146, 16.646, 'N', 'Linen', 'linen cabinet, floor to 84"'),
    ('toilet', F, F + 2.4, 20.25, 21.75, 'E', 'Toilet', ''),
    ('vanity', 3.0, 7.0, 23.6, 25.354, 'S', 'Vanity', '48" vanity, one sink'),
    # Bedroom 2: queen, headboard on the west wall
    ('bed', F, F + 6.67, 30.5, 35.5, 'E', 'Queen bed', ''),
    ('nightstand', F, F + 1.5, 28.8, 30.3, 'E', 'Nightstand', ''),
    ('nightstand', F, F + 1.5, 35.7, 37.2, 'E', 'Nightstand', ''),
    ('dresser', 9.0, 11.85, 38.04, 39.542, 'S', 'Dresser', ''),
    # Living room: TV on wall 5, L-sectional facing it, coffee table
    ('tv', 12.146, 12.4, 5.0, 9.0, 'E', 'TV', '65" TV on wall 5'),
    ('sofa', 19.0, 22.0, 2.5, 11.0, 'W', 'Sectional', ''),
    ('sofa', 15.5, 19.0, 8.0, 11.0, 'S', 'Sectional return', ''),
    ('coffee', 15.0, 17.5, 3.5, 7.0, 'N', 'Coffee table', ''),
    # Dining: 3'-6" x 7' table, 8 seats
    ('table', 15.75, 19.25, 26.0, 33.0, 'N', 'Dining table', ''),
    # Kitchen
    ('island', 24.5, 28.0, 25.5, 32.0, 'W', 'Island', 'sink and dishwasher, seating on the dining side'),
    ('counter', 31.854, 33.854, 27.8, 35.0, 'W', 'Counter', 'wall run on wall 15: range between base cabinets, uppers above'),
    ('range', 31.854, 33.854, 29.75, 32.25, 'W', 'Range', '30" electric range, ducted hood above'),
    ('fridge', 28.3, 31.3, 32.354, 34.854, 'S', 'Refrigerator', '36" refrigerator, ice maker'),
    ('counter', 23.0, 27.854, 37.542, 39.542, 'S', 'Counter', 'rear run under the window, uppers either side'),
    ('shelves', 28.146, 33.854, 38.042, 39.542, 'S', 'Pantry shelves', ''),
    ('shelves', 32.354, 33.854, 35.146, 38.042, 'W', 'Pantry shelves', ''),
    # Mud / laundry: washer and dryer on wall 13, bench and hooks on wall 11, linen tower
    ('washer', 33.354, 35.854, 1.0, 3.5, 'W', 'Washer', 'front load'),
    ('dryer', 33.354, 35.854, 3.6, 6.1, 'W', 'Dryer', 'front load, 30A 240V'),
    ('linen', 33.854, 35.854, 7.4, 9.854, 'W', 'Linen', 'linen / broom cabinet'),
    ('bench', 28.146, 29.646, 1.0, 6.0, 'E', 'Mud bench', 'bench with hooks above'),
    # Primary bedroom: king, headboard on wall 16
    ('bed', 41.2, 47.854, 29.8, 36.13, 'W', 'King bed', ''),
    ('nightstand', 46.354, 47.854, 28.0, 29.5, 'W', 'Nightstand', ''),
    ('nightstand', 46.354, 47.854, 36.43, 37.93, 'W', 'Nightstand', ''),
    ('dresser', 37.5, 43.0, 24.146, 25.646, 'N', 'Dresser', ''),
    ('tv', 34.146, 34.4, 30.97, 34.97, 'E', 'TV', '55" TV on wall 15'),
    # Primary bath: double vanity on wall 16, shower in the south-east corner, toilet on the east wall
    ('vanity', 48.146, 49.896, 28.4, 33.854, 'E', 'Double vanity', '66" double vanity'),
    ('shower', 53.542, 57.542, 29.354, 33.854, 'W', 'Shower', '4\'-0" x 4\'-6" tiled shower, glass door; valve on wall 17'),
    ('toilet', 55.142, 57.542, 25.0, 26.5, 'W', 'Toilet', ''),
    # WIC: rod and shelf on the north and west walls
    ('rods', 48.646, 57.542, 37.542, 39.542, 'S', 'Rod and shelf', ''),
    ('rods', 48.146, 50.146, 34.146, 37.4, 'E', 'Rod and shelf', ''),
    # Garage: two cars, attic pull-down stair
    ('car', 38.2, 44.6, 2.0, 18.0, 'S', 'Car', ''),
    ('car', 46.0, 52.4, 1.5, 17.0, 'S', 'Car', ''),
    ('stair', 40.0, 41.83, 19.0, 23.5, 'N', 'Attic access', '22" x 54" insulated pull-down attic stair; the way to FAU-1'),
    # Mechanical room
    ('wh', 55.6, 57.6, 21.5, 23.5, 'W', 'Water heater', '50 gal electric, in a drain pan, on a stand'),
]
