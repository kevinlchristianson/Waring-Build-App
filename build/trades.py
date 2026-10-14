"""Waring Build: electrical (E-1), plumbing (P-1) and HVAC (M-1) as data, in plan feet (see plan.py)."""
import math

# ============================================================================ E-1 electrical
# Panel MP: 200A main breaker load centre, 40 space, in the garage mechanical room.
# Circuits: key, load, breaker, wire, serves
CIRCUITS = [
    ('1', 'Gas range (igniter, oven, clock)', '20A AFCI/GFCI', '#12 Cu', 'kitchen, wall 15; space 2 left spare'),
    ('3-4', 'Dryer', '240V 30A 2P', '#10 Cu NM (4-wire)', 'mud / laundry'),
    ('5', 'Gas water heater (power-vent blower)', '20A GFCI', '#12 Cu', 'mechanical room; space 6 left spare'),
    ('7-8', 'Air conditioner AC-1 (outdoor unit)', '240V 25A 2P (per nameplate MOCP)', '#10 Cu', 'east wall, disconnect at the unit'),
    ('9', 'Gas furnace FAU-1 (blower, inducer, controls)', '120V 15A', '#14 Cu', 'attic, service switch at the unit; space 10 left spare'),
    ('11', 'Kitchen small appliance 1', '20A AFCI/GFCI', '#12 Cu', 'kitchen counters: rear run, wall run south'),
    ('12', 'Kitchen small appliance 2', '20A AFCI/GFCI', '#12 Cu', 'kitchen counters: wall run north, island'),
    ('13', 'Dishwasher', '20A AFCI/GFCI', '#12 Cu', 'island'),
    ('14', 'Disposal', '20A AFCI/GFCI', '#12 Cu', 'island'),
    ('15', 'Refrigerator', '20A AFCI', '#12 Cu', 'kitchen'),
    ('16', 'Laundry', '20A AFCI/GFCI', '#12 Cu', 'washer and laundry receptacles (210.11(C)(2))'),
    ('17', 'Bath 2 receptacles', '20A GFCI', '#12 Cu', 'Bath 2 (210.11(C)(3))'),
    ('18', 'Primary bath receptacles', '20A GFCI', '#12 Cu', 'primary bath (210.11(C)(3))'),
    ('19', 'Bedroom 3 and hall receptacles', '15A AFCI', '#14 Cu', 'Bedroom 3, hall'),
    ('20', 'Bedroom 2 receptacles', '15A AFCI', '#14 Cu', 'Bedroom 2'),
    ('21', 'Primary bedroom and WIC receptacles', '15A AFCI', '#14 Cu', 'primary bedroom, WIC'),
    ('22', 'Living room receptacles', '15A AFCI', '#14 Cu', 'living room'),
    ('23', 'Dining and back hall receptacles', '20A AFCI', '#12 Cu', 'dining, back hall'),
    ('24', 'Lighting, bedroom wing', '15A AFCI', '#14 Cu', 'Bedrooms 2 and 3, hall, Bath 2 lights and fan, smoke alarms'),
    ('25', 'Lighting, great room', '15A AFCI', '#14 Cu', 'living, dining, kitchen, pantry, back hall, laundry, porch and patio'),
    ('26', 'Lighting, primary suite and garage', '15A AFCI', '#14 Cu', 'primary suite, garage, mechanical room, attic, garage coach lights'),
    ('27', 'Garage receptacles', '20A GFCI', '#12 Cu', 'garage, attic service receptacle (210.11(C)(4), 210.63)'),
    ('28', 'Garage door opener', '20A GFCI', '#12 Cu', 'opener receptacle in the garage ceiling'),
    ('29', 'Exterior receptacles', '20A GFCI', '#12 Cu', 'porch, patio, AC-1 service receptacle (210.63)'),
]
# device types: what each draws as on E-1, and its bill-of-materials line
DEV = {
    'rec': 'duplex receptacle, 15A, tamper resistant',
    'usb': 'duplex receptacle, 15A, tamper resistant, with USB-A/C',
    'rec20': 'duplex receptacle, 20A, tamper resistant',
    'gfci': 'GFCI receptacle, 20A, tamper resistant',
    'wp': 'GFCI receptacle, 20A, weather resistant, in-use cover',
    'ded': 'dedicated receptacle, 20A',
    'r240': '240V receptacle / appliance connection',
    'floor': 'floor box with duplex receptacle, 15A',
    'tv': 'TV box: duplex receptacle and low-voltage pass-through',
    'sw': 'single-pole switch, rocker',
    'sw3': '3-way switch, rocker',
    'dim': 'dimmer, rocker, LED rated',
    'fansw': 'fan speed control and light switch (2-gang)',
    'tmr': 'timer switch for the exhaust fan',
    'can': '6" recessed LED wafer, 3000K, IC',
    'wet': '6" recessed LED wafer, 3000K, IC, wet location',
    'surf': 'surface LED ceiling fixture, 3000K',
    'shop': '4\' LED shop light, 4000K',
    'pend': 'pendant over the island',
    'chand': 'chandelier box, dimmable',
    'fanbox': 'fan-rated ceiling box, ceiling fan with light kit',
    'sconce': 'vanity light bar over the mirror',
    'strip': 'under-cabinet LED strip with driver',
    'ext': 'exterior wall light, wet location, dusk-to-dawn',
    'soffit': 'exterior soffit downlight, wet location',
    'ef': 'bath exhaust fan, 80 CFM, 0.8 sone, ducted to a roof cap',
    'hood': 'range hood, 300 CFM, ducted 6" to a roof cap',
    'smoke': 'smoke alarm, hardwired, interconnected, battery backup',
    'combo': 'smoke / CO alarm, hardwired, interconnected, battery backup',
    'data': 'Cat6 data outlet',
    'wap': 'Cat6 drop for a ceiling wireless access point',
    'bell': 'video doorbell (low voltage, transformer in the mech room)',
    'chime': 'door chime',
    'panel': 'main panel MP, 200A main breaker, 40 space',
    'media': 'structured media enclosure, 28"',
    'disc': 'AC disconnect, fused / non-fused per nameplate',
    'jbox': 'junction box, hardwired appliance',
    'opener': 'ceiling receptacle for the garage door opener, 20A GFCI',
    'attic': 'attic light at the furnace, switched at the access with a pilot light (M1305.1.3.1)',
}
LETTER = {'rec': 'R', 'usb': 'R', 'rec20': 'R', 'gfci': 'R', 'wp': 'R', 'ded': 'R', 'r240': 'R', 'floor': 'R', 'tv': 'R', 'opener': 'R', 'jbox': 'R',
          'sw': 'S', 'sw3': 'S', 'dim': 'S', 'fansw': 'S', 'tmr': 'S',
          'can': 'L', 'wet': 'L', 'surf': 'L', 'shop': 'L', 'pend': 'L', 'chand': 'L', 'fanbox': 'L', 'sconce': 'L', 'strip': 'L', 'ext': 'L', 'soffit': 'L', 'ef': 'L', 'hood': 'L', 'attic': 'L',
          'smoke': 'A', 'combo': 'A', 'data': 'T', 'wap': 'T', 'bell': 'T', 'chime': 'T', 'panel': 'X', 'media': 'X', 'disc': 'X'}
CEILING = {'can', 'wet', 'surf', 'shop', 'pend', 'chand', 'fanbox', 'ef', 'smoke', 'combo', 'wap', 'opener', 'attic', 'soffit'}

_raw = []


def dev(t, x, y, side, h, ckt, room, note='', leg='', legend=''):
    _raw.append(dict(type=t, x=round(x, 3), y=round(y, 3), side=side, h=h, ckt=ckt, room=room, note=note, leg=leg, legend=legend or DEV[t]))


IN = 3.5 / 12 / 2  # half an interior wall
# ---- mechanical room: panel, media, water heater
dev('panel', 52.146, 21.0, 'E', 60, 'panel', 'Mech Room', 'Main panel MP on wall 20, garage-side mech room; 30" x 36" working space in front (110.26), service entrance from the meter on the east wall')
dev('media', 57.542, 19.6, 'W', 60, 'data', 'Mech Room', 'Structured media enclosure on wall 2: every Cat6 home run lands here; doorbell transformer beside it')
dev('ded', 57.542, 22.5, 'W', 60, '5', 'Mech Room', 'Water heater: receptacle for the power-vent blower, above the tank on wall 2')
dev('surf', 54.9, 20.5, 'c', 108, '26', 'Mech Room', leg='mech')
dev('sw', 56.3, 18.146, 'N', 48, '26', 'Mech Room', 'inside, latch side of D16', leg='mech')
# ---- outside the east wall: air conditioner
dev('disc', 58.0, 20.4, 'E', 48, '7-8', 'Exterior', 'AC-1 disconnect on the east wall, within sight of the unit')
dev('wp', 58.0, 22.3, 'E', 24, '29', 'Exterior', 'service receptacle within 25\' of AC-1 (210.63)')
# ---- Bedroom 3
dev('usb', 0.458, 2.55, 'E', 16, '19', 'Bedroom 3', 'nightstand, south side of the bed')
dev('usb', 0.458, 9.45, 'E', 16, '19', 'Bedroom 3', 'nightstand, north side of the bed')
dev('rec', 11.854, 6.4, 'W', 16, '19', 'Bedroom 3')
dev('rec', 10.4, 0.458, 'N', 16, '19', 'Bedroom 3', 'behind the dresser, for a TV on it')
dev('data', 10.9, 0.458, 'N', 16, 'data', 'Bedroom 3')
dev('fanbox', 6.16, 6.4, 'c', 108, '24', 'Bedroom 3', 'centre of the room', leg='bed3')
dev('fansw', 8.2, 12.354, 'S', 48, '24', 'Bedroom 3', 'latch side of D6', leg='bed3')
dev('smoke', 6.0, 10.6, 'c', 108, '24', 'Bedroom 3')
# ---- Bedroom 2
dev('usb', 0.458, 29.55, 'E', 16, '20', 'Bedroom 2', 'nightstand, south side of the bed')
dev('usb', 0.458, 36.45, 'E', 16, '20', 'Bedroom 2', 'nightstand, north side of the bed')
dev('rec', 11.854, 33.8, 'W', 16, '20', 'Bedroom 2')
dev('rec', 10.4, 39.542, 'S', 16, '20', 'Bedroom 2', 'behind the dresser, for a TV on it')
dev('data', 10.9, 39.542, 'S', 16, 'data', 'Bedroom 2')
dev('fanbox', 6.16, 33.84, 'c', 108, '24', 'Bedroom 2', 'centre of the room', leg='bed2')
dev('fansw', 8.2, 28.146, 'N', 48, '24', 'Bedroom 2', 'latch side of D10', leg='bed2')
dev('smoke', 6.0, 29.7, 'c', 108, '24', 'Bedroom 2')
# ---- hall
dev('can', 10.0, 16.0, 'c', 108, '24', 'Hall', leg='hall')
dev('can', 10.0, 24.5, 'c', 108, '24', 'Hall', leg='hall')
dev('sw3', 8.146, 14.0, 'E', 48, '24', 'Hall', 'south end, by D6', leg='hall')
dev('sw3', 8.146, 26.6, 'E', 48, '24', 'Hall', 'north end, by D10', leg='hall')
dev('rec', 8.146, 23.0, 'E', 16, '19', 'Hall', 'hall over 10\' long (210.52(H))')
dev('combo', 10.0, 20.4, 'c', 108, '24', 'Hall', 'outside the bedrooms')
dev('wap', 10.0, 22.4, 'c', 108, 'data', 'Hall', 'wireless access point, bedroom wing')
# ---- Bath 2
dev('gfci', 6.6, 25.354, 'S', 42, '17', 'Bath 2', 'above the vanity backsplash, within 3\' of the basin')
dev('sconce', 5.0, 25.354, 'S', 84, '24', 'Bath 2', 'over the mirror', leg='bath2')
dev('wet', 5.35, 16.4, 'c', 108, '24', 'Bath 2', 'over the tub', leg='bath2')
dev('ef', 2.6, 19.4, 'c', 108, '24', 'Bath 2', 'between the toilet and the tub', leg='bath2-fan')
dev('sw', 7.854, 22.0, 'W', 48, '24', 'Bath 2', 'latch side of D8: 3-gang with the next two', leg='bath2')
dev('tmr', 7.854, 22.4, 'W', 48, '24', 'Bath 2', 'fan timer', leg='bath2-fan')
# ---- living room
dev('rec', 17.8, 4.458, 'N', 16, '22', 'Living Room')
dev('tv', 12.146, 7.0, 'E', 54, '22', 'Living Room', 'behind the TV on wall 5')
dev('data', 12.146, 7.5, 'E', 54, 'data', 'Living Room', 'behind the TV: 2 x Cat6')
dev('rec', 12.146, 14.6, 'E', 16, '22', 'Living Room')
dev('rec', 29.854, 6.0, 'W', 16, '22', 'Living Room')
dev('floor', 22.4, 6.75, 'c', 0, '22', 'Living Room', 'floor box behind the sectional, for lamps')
for x in (15.3, 20.5, 25.2):
    for y in (4.6, 13.0):
        dev('can', x, y, 'c', 108, '25', 'Living Room', leg='living')
dev('dim', 23.0, 4.458, 'N', 48, '25', 'Living Room', 'front door, latch side of D1: 3-gang (living cans 3-way, porch, garage coach lights)', leg='living')
dev('sw', 22.6, 4.458, 'N', 48, '25', 'Living Room', 'front door bank', leg='porch')
dev('sw', 22.2, 4.458, 'N', 48, '26', 'Living Room', 'front door bank', leg='coach')
dev('sw3', 29.854, 8.6, 'W', 48, '25', 'Living Room', 'living cans, kitchen side', leg='living')
dev('combo', 20.5, 9.0, 'c', 108, '24', 'Living Room', 'great room, over 20\' from the range')
dev('wap', 24.0, 16.5, 'c', 108, 'data', 'Living Room', 'wireless access point, great room')
dev('bell', 27.0, 4.0, 'S', 48, 'data', 'Exterior', 'video doorbell beside D1')
# ---- porch and patio
dev('soffit', 16.5, 1.0, 'c', 108, '25', 'Front Porch', leg='porch')
dev('soffit', 23.5, 1.0, 'c', 108, '25', 'Front Porch', leg='porch')
dev('ext', 27.2, 4.0, 'S', 72, '25', 'Front Porch', 'beside the front door', leg='porch')
dev('wp', 13.2, 4.0, 'S', 16, '29', 'Front Porch')
dev('soffit', 16.0, 41.0, 'c', 108, '25', 'Rear Patio', leg='patio')
dev('soffit', 21.0, 41.0, 'c', 108, '25', 'Rear Patio', leg='patio')
dev('wp', 24.0, 40.0, 'N', 16, '29', 'Rear Patio')
dev('ext', 38.0, 0.0, 'S', 84, '26', 'Exterior', 'coach light, west of the garage door', leg='coach')
dev('ext', 56.0, 0.0, 'S', 84, '26', 'Exterior', 'coach light, east of the garage door', leg='coach')
# ---- dining
dev('rec', 12.146, 25.8, 'E', 16, '23', 'Dining')
dev('rec', 12.146, 35.0, 'E', 16, '23', 'Dining')
dev('rec', 21.6, 35.542, 'S', 16, '23', 'Dining')
dev('chand', 17.5, 29.5, 'c', 96, '25', 'Dining', 'over the table centre', leg='dining')
dev('dim', 12.146, 22.0, 'E', 48, '25', 'Dining', 'north of the cased opening', leg='dining')
dev('sw', 13.6, 35.542, 'S', 48, '25', 'Dining', 'beside D2', leg='patio')
# ---- kitchen
dev('gfci', 23.8, 39.542, 'S', 44, '11', 'Kitchen', 'rear run')
dev('gfci', 27.5, 39.542, 'S', 44, '11', 'Kitchen', 'rear run, east of the window')
dev('gfci', 33.854, 28.6, 'W', 44, '11', 'Kitchen', 'wall run, south of the range')
dev('gfci', 33.854, 34.2, 'W', 44, '12', 'Kitchen', 'wall run, north of the range')
dev('ded', 33.854, 31.0, 'W', 4, '1', 'Kitchen', '120V receptacle behind the gas range, beside the gas stub')
dev('hood', 33.6, 31.0, 'W', 66, '25', 'Kitchen', 'range hood under the upper cabinet', leg='hood')
dev('gfci', 28.0, 26.6, 'E', 30, '12', 'Kitchen', 'island, east face, south end')
dev('gfci', 28.0, 31.2, 'E', 30, '12', 'Kitchen', 'island, east face, north end')
dev('ded', 27.6, 26.9, 'c', 6, '13', 'Kitchen', 'dishwasher, in the sink base')
dev('ded', 27.6, 28.75, 'c', 12, '14', 'Kitchen', 'disposal, switched at the sink')
dev('ded', 29.8, 34.854, 'S', 48, '15', 'Kitchen', 'behind the refrigerator')
dev('strip', 33.0, 28.75, 'W', 54, '25', 'Kitchen', 'under the wall-run uppers, south', leg='undercab')
dev('strip', 33.0, 33.6, 'W', 54, '25', 'Kitchen', 'under the wall-run uppers, north', leg='undercab')
dev('strip', 23.7, 38.8, 'S', 54, '25', 'Kitchen', 'under the rear-run uppers', leg='undercab')
dev('pend', 26.25, 27.2, 'c', 78, '25', 'Kitchen', 'over the island', leg='pendants')
dev('pend', 26.25, 30.3, 'c', 78, '25', 'Kitchen', 'over the island', leg='pendants')
for x, y in ((30.0, 22.5), (25.5, 22.5), (29.9, 27.0), (29.9, 31.0), (25.4, 35.0), (30.5, 36.9)):
    dev('can', x, y, 'c', 108, '25', 'Kitchen', leg='kitchen')
dev('dim', 34.6, 23.854, 'S', 48, '25', 'Kitchen', 'kitchen bank on wall 14 in the back-hall alcove: 4-gang', leg='kitchen')
dev('dim', 35.0, 23.854, 'S', 48, '25', 'Kitchen', 'kitchen bank', leg='pendants')
dev('sw', 35.4, 23.854, 'S', 48, '25', 'Kitchen', 'kitchen bank', leg='undercab')
dev('sw', 28.0, 28.0, 'E', 36, '14', 'Kitchen', 'disposal switch in the island face, beside the sink')
# ---- pantry
dev('surf', 31.0, 37.4, 'c', 108, '25', 'Pantry', leg='pantry')
dev('sw', 27.854, 39.1, 'W', 48, '25', 'Pantry', 'kitchen side, latch side of D15', leg='pantry')
# ---- back hall
dev('can', 30.6, 12.4, 'c', 108, '25', 'Back Hall', leg='backhall')
dev('can', 31.2, 16.6, 'c', 108, '25', 'Back Hall', leg='backhall')
dev('can', 35.0, 21.0, 'c', 108, '25', 'Back Hall', leg='backhall')
dev('sw3', 35.854, 19.0, 'W', 48, '25', 'Back Hall', 'latch side of D3: 2-gang with the garage lights', leg='backhall')
dev('sw3', 35.854, 18.6, 'W', 48, '26', 'Back Hall', 'garage lights, house side', leg='garage')
dev('sw3', 33.4, 10.146, 'N', 48, '25', 'Back Hall', 'by D11', leg='backhall')
dev('rec', 35.854, 14.0, 'W', 16, '23', 'Back Hall')
dev('combo', 35.0, 22.4, 'c', 108, '24', 'Back Hall', 'by the garage door and the primary suite')
dev('chime', 34.4, 10.146, 'N', 84, 'data', 'Back Hall')
# ---- mud / laundry
dev('gfci', 35.854, 2.25, 'W', 42, '16', 'Mud / Laundry', 'washer, beside the washer box')
dev('r240', 35.854, 4.85, 'W', 30, '3-4', 'Mud / Laundry', 'dryer, NEMA 14-30R')
dev('gfci', 31.5, 0.458, 'N', 42, '16', 'Mud / Laundry', 'over the bench')
dev('surf', 32.0, 5.0, 'c', 108, '25', 'Mud / Laundry', leg='laundry')
dev('sw', 33.4, 9.854, 'S', 48, '25', 'Mud / Laundry', 'latch side of D11', leg='laundry')
# ---- primary bedroom
dev('usb', 47.854, 27.6, 'W', 16, '21', 'Primary Bedroom', 'nightstand, south side of the bed')
dev('usb', 47.854, 38.4, 'W', 16, '21', 'Primary Bedroom', 'nightstand, north side of the bed')
dev('tv', 34.146, 33.0, 'E', 54, '21', 'Primary Bedroom', 'behind the TV on wall 15')
dev('data', 34.146, 33.5, 'E', 54, 'data', 'Primary Bedroom', 'behind the TV')
dev('rec', 34.146, 29.0, 'E', 16, '21', 'Primary Bedroom')
dev('rec', 34.146, 37.4, 'E', 16, '21', 'Primary Bedroom')
dev('rec', 37.6, 39.542, 'S', 16, '21', 'Primary Bedroom')
dev('rec', 44.6, 39.542, 'S', 16, '21', 'Primary Bedroom')
dev('rec', 40.25, 24.146, 'N', 16, '21', 'Primary Bedroom', 'behind the dresser')
dev('rec', 45.5, 24.146, 'N', 16, '21', 'Primary Bedroom')
dev('fanbox', 41.0, 31.84, 'c', 108, '26', 'Primary Bedroom', 'centre of the room', leg='primary')
dev('fansw', 34.146, 27.7, 'E', 48, '26', 'Primary Bedroom', 'latch side of D12', leg='primary')
dev('smoke', 37.5, 28.0, 'c', 108, '24', 'Primary Bedroom')
# ---- primary bath
dev('gfci', 48.146, 31.1, 'E', 42, '18', 'Primary Bath', 'between the basins, above the backsplash')
dev('sconce', 48.146, 29.75, 'E', 84, '26', 'Primary Bath', 'over the south basin', leg='pbath')
dev('sconce', 48.146, 32.5, 'E', 84, '26', 'Primary Bath', 'over the north basin', leg='pbath')
dev('wet', 55.54, 31.6, 'c', 108, '26', 'Primary Bath', 'in the shower', leg='pbath-can')
dev('can', 52.0, 27.0, 'c', 108, '26', 'Primary Bath', leg='pbath-can')
dev('ef', 54.4, 27.4, 'c', 108, '26', 'Primary Bath', 'runs continuous at 50 CFM for whole-house ventilation (M1505.4), boost to 80', leg='pbath-fan')
dev('sw', 48.146, 27.7, 'E', 48, '26', 'Primary Bath', 'latch side of D13: 3-gang', leg='pbath')
dev('sw', 48.146, 28.1, 'E', 48, '26', 'Primary Bath', '3-gang', leg='pbath-can')
dev('tmr', 48.146, 28.5, 'E', 48, '26', 'Primary Bath', 'fan control: continuous low, boost timer', leg='pbath-fan')
# ---- WIC
dev('surf', 53.0, 36.9, 'c', 108, '26', 'WIC', leg='wic')
dev('sw', 53.7, 33.854, 'S', 48, '26', 'WIC', 'bath side, latch side of D14', leg='wic')
dev('rec', 57.542, 36.0, 'W', 16, '21', 'WIC')
# ---- garage and attic
dev('gfci', 36.146, 6.0, 'E', 48, '27', 'Garage')
dev('gfci', 36.146, 15.0, 'E', 48, '27', 'Garage')
dev('gfci', 46.0, 23.854, 'S', 48, '27', 'Garage')
dev('gfci', 57.542, 4.0, 'W', 48, '27', 'Garage')
dev('opener', 47.0, 12.5, 'c', 108, '28', 'Garage', 'opener receptacle; push button by D3, safety eyes at the door')
for x, y in ((41.0, 7.0), (41.0, 14.5), (50.5, 7.0), (50.5, 13.0)):
    dev('shop', x, y, 'c', 108, '26', 'Garage', leg='garage')
dev('sw3', 36.146, 18.9, 'E', 48, '26', 'Garage', 'garage side of D3', leg='garage')
dev('sw3', 57.542, 11.0, 'W', 48, '26', 'Garage', 'latch side of D5', leg='garage')
dev('sw', 43.0, 23.854, 'S', 54, '26', 'Garage', 'by the attic stair, with a pilot light', leg='attic')
dev('attic', 31.6, 12.0, 'c', 120, '26', 'Attic', 'at FAU-1, on the service platform', leg='attic')
dev('gfci', 33.0, 12.0, 'c', 120, '27', 'Attic', 'service receptacle at FAU-1 (210.63)')
dev('disc', 29.2, 13.0, 'c', 120, '9', 'Attic', 'FAU-1 service switch at the unit (toggle disconnect, M1305.1.3)')

# give tags: R1.., S1.., L1.., A1.., T1.., X1..
DEVICES = []
_count = {}
for d in _raw:
    k = LETTER[d['type']]
    _count[k] = _count.get(k, 0) + 1
    d['id'] = f'{k}{_count[k]}'
    DEVICES.append(d)

LEGS = [
    ('mech', 'Mech room light', 'Mech Room', 'switch inside the door'),
    ('bed3', 'Bedroom 3 fan and light', 'Bedroom 3', 'fan speed and light at D6'),
    ('bed2', 'Bedroom 2 fan and light', 'Bedroom 2', 'fan speed and light at D10'),
    ('hall', 'Hall cans', 'Hall', '3-way: each end of the hall'),
    ('bath2', 'Bath 2 lights', 'Bath 2', 'vanity light and tub can on one switch at D8'),
    ('bath2-fan', 'Bath 2 fan', 'Bath 2', 'timer at D8'),
    ('living', 'Living room cans', 'Living Room', '3-way dimmer: front door and the kitchen side of wall 11'),
    ('porch', 'Porch lights', 'Front Porch', 'at the front door'),
    ('coach', 'Garage coach lights', 'Exterior', 'at the front door; dusk-to-dawn sensors in the fixtures'),
    ('patio', 'Patio lights', 'Rear Patio', 'beside D2'),
    ('dining', 'Dining chandelier', 'Dining', 'dimmer on wall 5'),
    ('kitchen', 'Kitchen cans', 'Kitchen', 'dimmer on wall 14, back-hall alcove'),
    ('pendants', 'Island pendants', 'Kitchen', 'dimmer on wall 14'),
    ('undercab', 'Under-cabinet lights', 'Kitchen', 'switch on wall 14'),
    ('hood', 'Range hood', 'Kitchen', 'controls on the hood'),
    ('pantry', 'Pantry light', 'Pantry', 'kitchen side of D15'),
    ('backhall', 'Back hall cans', 'Back Hall', '3-way: D3 and D11'),
    ('laundry', 'Laundry light', 'Mud / Laundry', 'at D11'),
    ('primary', 'Primary bedroom fan and light', 'Primary Bedroom', 'fan speed and light at D12'),
    ('pbath', 'Primary bath vanity lights', 'Primary Bath', 'at D13'),
    ('pbath-can', 'Primary bath cans', 'Primary Bath', 'at D13'),
    ('pbath-fan', 'Primary bath fan', 'Primary Bath', 'continuous low with a boost timer at D13'),
    ('wic', 'WIC light', 'WIC', 'bath side of D14'),
    ('garage', 'Garage lights', 'Garage', '3-way: D3 (house side and garage side) and D5'),
    ('attic', 'Attic light', 'Attic', 'switch with a pilot light by the attic stair'),
]

# ============================================================================ P-1 plumbing
# Fixtures: drain point (where the trap arm meets the wall or floor), supply, DFU (IRC Table P3004.1)
PFIX = [
    dict(id='F1', name='Bath 2 toilet', kind='wc', x=1.458, y=21.0, dfu=3, trap='3"', hot=False, cold=True, vent='V1', h=8, note='1.28 gpf, 12" rough from the west wall; supply up through the slab, not in the exterior wall'),
    dict(id='F2', name='Bath 2 lavatory', kind='lav', x=5.0, y=25.354, dfu=1, trap='1-1/4"', hot=True, cold=True, vent='V1', h=20, note='trap arm into wall 9, vent V1 rises behind it'),
    dict(id='F3', name='Bath 2 tub / shower', kind='tub', x=7.354, y=16.4, dfu=2, trap='1-1/2"', hot=True, cold=True, vent='V1', h=48, note='drain at the east end; valve and shower riser on wall 8 (hall side access panel optional)'),
    dict(id='F4', name='Kitchen sink (island)', kind='sink', x=26.9, y=28.75, dfu=2, trap='1-1/2"', hot=True, cold=True, vent='AAV', h=20, note='double bowl with disposal; air admittance valve in the sink base (P3114), or an island loop vent if the AHJ requires'),
    dict(id='F5', name='Dishwasher', kind='dw', x=27.4, y=26.9, dfu=2, trap='via F4', hot=True, cold=False, vent='AAV', h=6, note='high loop to the disposal'),
    dict(id='F6', name='Refrigerator ice maker', kind='ice', x=29.8, y=34.854, dfu=0, trap='—', hot=False, cold=True, vent='—', h=10, note='recessed ice-maker box in wall 19, 1/4-turn valve'),
    dict(id='F7', name='Washer', kind='washer', x=35.854, y=2.25, dfu=2, trap='2"', hot=True, cold=True, vent='V3', h=42, note='recessed washer box in wall 13 with a 2" standpipe; wall 13 faces the unheated garage: PEX on the warm side of the insulation'),
    dict(id='F8', name='Primary lavatory, south', kind='lav', x=48.146, y=29.75, dfu=1, trap='1-1/4"', hot=True, cold=True, vent='V2', h=20, note='trap arm into wall 16'),
    dict(id='F9', name='Primary lavatory, north', kind='lav', x=48.146, y=32.5, dfu=1, trap='1-1/4"', hot=True, cold=True, vent='V2', h=20, note='trap arm into wall 16'),
    dict(id='F10', name='Primary shower', kind='shower', x=55.54, y=31.6, dfu=2, trap='2"', hot=True, cold=True, vent='V2', h=48, note='centre drain, PVC liner or a foam pan; valve on wall 17 at 48", head at 80"'),
    dict(id='F11', name='Primary toilet', kind='wc', x=56.542, y=25.75, dfu=3, trap='3"', hot=False, cold=True, vent='V2', h=8, note='1.28 gpf, 12" rough from the east wall; supply up through the slab'),
    dict(id='F12', name='Water heater', kind='wh', x=56.6, y=22.5, dfu=0, trap='—', hot=True, cold=True, vent='—', h=0, note='50 gal gas, power direct vent (sealed combustion, 2-pipe PVC through the roof), on an 18" stand in the garage (G2408.2), thermal expansion tank, T&P discharge to within 6" of the garage floor, in a drain pan'),
    dict(id='F13', name='Hose bib, front', kind='hb', x=33.6, y=0.458, dfu=0, trap='—', hot=False, cold=True, vent='—', h=24, note='frost-free sillcock through wall 25 from the laundry, vacuum breaker'),
    dict(id='F14', name='Hose bib, rear', kind='hb', x=27.2, y=39.542, dfu=0, trap='—', hot=False, cold=True, vent='—', h=24, note='frost-free sillcock through wall 3 from the rear counter base, vacuum breaker'),
]
# drains under the slab: (size, points, note)
DRAINS = [
    dict(id='BD', size='4"', pts=[(32.5, 29.25), (32.5, -4.0)], note='building drain, 1/4"/ft, out under the laundry and the front wall to the sewer / septic; cleanout CO1 outside'),
    dict(id='B1', size='3"', pts=[(1.458, 22.0), (32.5, 22.0)], note='Bath 2 branch, 1/4"/ft east under the hall and the great room to the building drain'),
    dict(id='B1a', size='3"', pts=[(1.458, 21.0), (1.458, 22.0)], note='F1 closet bend'),
    dict(id='B1b', size='1-1/2"', pts=[(5.0, 25.354), (5.0, 22.0)], note='F2 lav arm'),
    dict(id='B1c', size='1-1/2"', pts=[(7.354, 16.4), (7.354, 22.0)], note='F3 tub'),
    dict(id='B2', size='2"', pts=[(26.9, 28.75), (26.9, 22.0)], note='kitchen island: F4 and F5'),
    dict(id='B3', size='3"', pts=[(56.542, 29.25), (32.5, 29.25)], note='primary bath branch, west under the primary bedroom and the kitchen'),
    dict(id='B3a', size='3"', pts=[(56.542, 25.75), (56.542, 29.25)], note='F11 closet bend'),
    dict(id='B3b', size='2"', pts=[(55.54, 31.6), (55.54, 29.25)], note='F10 shower'),
    dict(id='B3c', size='1-1/2"', pts=[(48.4, 32.5), (48.4, 29.25)], note='F8 and F9 lavs'),
    dict(id='B4', size='2"', pts=[(35.5, 2.25), (32.5, 2.25)], note='F7 washer standpipe'),
]
CLEANOUTS = [
    ('CO1', 32.5, -3.0, 'two-way cleanout outside the front wall, at grade'),
    ('CO2', 6.0, 25.5, 'base of V1 in wall 9, 12" AFF, access behind the vanity'),
    ('CO3', 48.0, 31.1, 'base of V2 in wall 16, access in the vanity'),
    ('CO4', 26.9, 28.5, 'island sink trap, in the sink base'),
    ('CO5', 35.7, 2.25, 'washer standpipe'),
]
# vents: rise in the wall, then run in the attic to one 3" vent through the rear roof
VENTS = [
    dict(id='V1', size='2"', wall=9, base=(6.0, 25.5), attic=[(6.0, 25.5), (30.0, 25.5), (30.0, 27.0)], note='Bath 2 group: F1, F2, F3 wet-vented through the lav; dry vent up in wall 9'),
    dict(id='V2', size='2"', wall=16, base=(48.0, 31.1), attic=[(48.0, 31.1), (30.0, 31.1), (30.0, 27.0)], note='primary bath group: F8 to F11 wet-vented; dry vent up in wall 16'),
    dict(id='V3', size='2"', wall=13, base=(36.0, 2.9), attic=[(35.5, 2.9), (35.5, 25.5), (30.0, 25.5)], note='washer standpipe vent up in wall 13'),
]
VTR = dict(x=30.0, y=27.0, size='3"', note='one 3" vent through the roof on the rear slope, 6" above the roof, flashed boot (IRC P3103)')
AAV = dict(x=27.6, y=28.3, note='air admittance valve in the island sink base, 4" above the trap arm, accessible (P3114)')
# supply: PEX-A home runs from the manifold, under the slab in sleeves, no fittings below the slab
MANIFOLD = dict(x=57.3, y=19.6, note='PEX manifold on wall 2 in the mech room: hot and cold, a shutoff for every run')
SERVICE = dict(x=57.542, y=18.7, note='water service in, 1" PEX, main shutoff, pressure gauge, PRV if the street exceeds 80 psi')
TRUNKS = [
    dict(id='TW', pts=[(57.0, 19.6), (51.0, 19.6), (51.0, 22.75), (5.0, 22.75)], note='west home-run bundle under the garage slab and the house, in sleeves through the garage foundation; insulate under the garage slab'),
    dict(id='TP', pts=[(57.0, 20.0), (55.0, 20.0), (55.0, 28.6), (48.6, 28.6)], note='primary bath bundle, north under wall 14'),
    dict(id='TS', pts=[(35.0, 22.75), (35.0, 1.2)], note='laundry and front hose bib bundle'),
]
BRANCHES = [
    dict(fixture='F1', pts=[(5.0, 22.75), (1.2, 22.75), (1.2, 21.6)]),
    dict(fixture='F2', pts=[(5.0, 22.75), (5.3, 25.354)]),
    dict(fixture='F3', pts=[(7.0, 22.75), (8.0, 22.75), (8.0, 16.4)]),
    dict(fixture='F4', pts=[(27.2, 22.75), (27.2, 28.75)]),
    dict(fixture='F5', pts=[(27.6, 22.75), (27.6, 26.9)]),
    dict(fixture='F6', pts=[(30.2, 22.75), (30.2, 34.854)]),
    dict(fixture='F14', pts=[(26.6, 22.75), (26.6, 39.542), (27.2, 39.542)]),
    dict(fixture='F7', pts=[(35.0, 1.2), (35.0, 2.25), (35.854, 2.25)]),
    dict(fixture='F13', pts=[(35.0, 1.2), (33.6, 1.2), (33.6, 0.458)]),
    dict(fixture='F8', pts=[(48.6, 28.6), (48.146, 29.75)]),
    dict(fixture='F9', pts=[(48.6, 28.6), (48.6, 32.5), (48.146, 32.5)]),
    dict(fixture='F10', pts=[(55.0, 28.6), (55.5, 28.6), (55.5, 33.854)]),
    dict(fixture='F11', pts=[(55.0, 24.6), (56.6, 24.6), (56.6, 25.2)]),
    dict(fixture='F12', pts=[(57.0, 19.6), (56.6, 21.5)]),
]

# ============================================================================ M-1 HVAC
AH = dict(x1=29.5, x2=34.5, y1=12.75, y2=15.25, h=9.6,
          note='FAU-1: 96% AFUE two-stage condensing gas furnace, 60,000 BTU/h input, variable-speed blower, with a 2.5-ton cased A/C coil; listed for attic installation, horizontal on a platform over the back hall; 30" service platform at the access side, auxiliary drain pan with a float switch')
SUPPLY_PLENUM = (28.5, 29.5, 12.25, 15.75)
RETURN_PLENUM = (34.5, 35.5, 12.5, 15.5)
DTRUNKS = [
    dict(id='ST1', size='14x8', pts=[(28.5, 14.0), (10.0, 14.0)], note='west trunk in the attic, sheet metal, R-8 wrap; reduces to 10x8 past the living room take-offs'),
    dict(id='ST1b', size='10x8', pts=[(10.0, 14.0), (10.0, 26.0)], note='bedroom-wing trunk over the hall'),
    dict(id='ST2', size='14x8', pts=[(29.0, 15.75), (29.0, 30.5), (39.0, 30.5)], note='north trunk over the kitchen'),
    dict(id='ST2b', size='10x8', pts=[(39.0, 30.5), (53.0, 30.5)], note='primary-suite trunk'),
]
REGISTERS = [
    # id, room, x, y, cfm, flex, from (trunk point)
    ('G1', 'Bedroom 3', 6.0, 9.4, 100, '7"', (10.0, 14.0)),
    ('G2', 'Bath 2', 3.6, 19.4, 50, '6"', (10.0, 19.4)),
    ('G3', 'Bedroom 2', 6.0, 37.4, 100, '7"', (10.0, 26.0)),
    ('G4', 'Living Room', 15.3, 6.8, 100, '7"', (15.3, 14.0)),
    ('G5', 'Living Room', 24.0, 6.8, 100, '7"', (24.0, 14.0)),
    ('G6', 'Dining', 17.5, 33.6, 120, '8"', (29.0, 30.5)),
    ('G7', 'Kitchen', 26.0, 35.4, 130, '8"', (29.0, 30.5)),
    ('G8', 'Mud / Laundry', 31.6, 4.4, 50, '6"', (28.8, 12.25)),
    ('G9', 'Primary Bedroom', 39.0, 37.8, 80, '7"', (39.0, 30.5)),
    ('G10', 'Primary Bedroom', 39.0, 26.2, 70, '6"', (39.0, 30.5)),
    ('G11', 'Primary Bath', 51.6, 27.4, 70, '6"', (51.6, 30.5)),
    ('G12', 'WIC', 52.4, 37.2, 30, '5"', (52.4, 30.5)),
]
RETURNS = [
    dict(id='RG1', room='Back Hall', x=34.9, y=14.0, w=20 / 12, l=30 / 12, along_y=True, cfm=650, size='20x30 filter grille, MERV 8', route=[(34.9, 14.0), (35.0, 14.0)], note='central return under FAU-1, straight into the return plenum'),
    dict(id='RG2', room='Hall', x=10.0, y=21.0, w=16 / 12, l=25 / 12, along_y=True, cfm=350, size='16x25 filter grille, MERV 8', route=[(10.0, 21.0), (10.0, 16.6), (35.0, 16.6), (35.0, 15.5)], note='bedroom-wing return, 14" insulated flex to the return plenum'),
]
JUMPS = [
    ('J1', 'Bedroom 3', (9.6, 10.6), (9.8, 13.6), '10"'),
    ('J2', 'Bedroom 2', (9.6, 29.6), (9.8, 27.0), '10"'),
    ('J3', 'Primary Bedroom', (35.4, 25.6), (35.0, 23.0), '10"'),
]
TSTATS = [dict(id='T1', x=12.146, y=15.6, side='E', note='thermostat on wall 5, living-room side, 54" AFF; the hall return and the cased opening keep it in the house air')]
EXHAUST = [
    dict(id='EF1', name='Bath 2 fan', size='4"', pts=[(2.6, 19.4), (2.6, 23.0)], cap='roof cap, rear slope', cfm=80),
    dict(id='EF2', name='Primary bath fan', size='4"', pts=[(54.4, 27.4), (54.4, 26.0)], cap='roof cap, rear slope', cfm=80),
    dict(id='EF3', name='Range hood', size='6"', pts=[(33.0, 31.0), (33.0, 31.0)], cap='roof cap with damper, rear slope', cfm=300),
    dict(id='EF4', name='Dryer vent', size='4"', pts=[(35.6, 4.85), (35.6, 6.5)], cap='dryer roof cap, front slope; rigid metal, 11\' developed with 2 elbows (M1502.4.5)', cfm=0),
]
HP = dict(x1=58.6, x2=61.4, y1=19.6, y2=22.4, note='AC-1: 2.5-ton air conditioner (condensing unit) on a pad, 18" off the east wall')
LINESET = [(58.6, 21.0), (57.2, 21.0), (57.2, 20.6), (36.0, 20.6), (34.5, 15.0)]
CONDENSATE = [(29.6, 12.9), (35.6, 12.9), (35.6, 3.2)]

# Natural gas: meter on the garage east wall, into the garage, along the east wall into the mech room
# (main shutoff and drip leg there), up into the attic and west over the garage ceiling to FAU-1.
GAS_METER = dict(x=58.4, y=15.0, note='Gas meter and regulator on the garage east wall, set by the utility; regulator vent 3\' from the AC-1 unit, openings and the dryer exhaust')
GAS = [
    dict(id='GS1', size='3/4"', where='wall', pts=[(58.0, 15.0), (57.5, 15.0), (57.5, 18.8)],
         note='3/4" black steel (or CSST) from the meter, through the east wall and up the garage side of it, protected from vehicles, into the mech room'),
    dict(id='GS2', size='3/4"', where='riser', pts=[(57.5, 18.8)],
         note='Main gas shutoff and drip leg in the mech room; tee to the water heater, then up through the garage ceiling (fire-caulked)'),
    dict(id='GS4', size='1/2"', where='low', h=3.0, to=1.6, pts=[(57.5, 18.8), (57.5, 21.0), (56.6, 21.5)],
         note='1/2" black steel to the water heater in the mech room, shutoff and sediment trap at the unit'),
    dict(id='GS3', size='1/2"', where='attic', pts=[(57.5, 18.8), (37.2, 18.8), (37.2, 13.0), (34.6, 13.0)],
         note='1/2" CSST in the attic over the garage ceiling to FAU-1, about 30\', supported every 6\'; bonded with #6 Cu to the electrode system (G2411); shutoff and sediment trap within 6\' of the furnace'),
    dict(id='GS5', size='1/2"', where='attic', to=1.0, pts=[(37.2, 18.8), (37.2, 31.0), (34.0, 31.0)],
         note='1/2" CSST tee off GS3 in the attic, north over the primary bedroom ceiling, down inside wall 15 to a shutoff behind the range, 12" AFF'),
]
FLUES = [
    dict(id='V1', name='Furnace vent', pts=[(33.0, 15.0), (33.0, 21.6)], note='FAU-1 vent and combustion air: 2" PVC intake and exhaust (direct vent, sealed combustion), up through the rear roof slope with a concentric termination 12" above the roof and the snow line; slope back to the furnace'),
    dict(id='V2', name='Water heater vent', pts=[(56.6, 22.5), (56.6, 22.5)], note='Water heater vent and combustion air: 2" or 3" PVC per the manual (power direct vent), up through the garage ceiling and the rear roof slope, concentric termination 12" above the roof and the snow line'),
]
