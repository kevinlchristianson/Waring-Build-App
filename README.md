# Waring Build Contractor App

A phone-friendly contractor app for the Waring Build house: 3 bed, 2 bath, 1,800 sq ft conditioned, single story on a slab, with a 2-car garage (58' x 40' overall). It follows the 7824 Zero Rd app: one `index.html` with a 3D model and four trade sheets, plus crew chat.

| Tab | What it shows |
| --- | --- |
| 3D | The house, with layers for walls, framing, electrical, plumbing, HVAC, trusses, roof and furniture. Click anything to read it. |
| S-1 Framing | Walls, openings, headers, blocking, lumber, drywall and roof framing |
| E-1 Electrical | 200A panel MP in the garage mech room, 29 circuits, every device, switch legs, one sheet per circuit |
| P-1 Plumbing | Drains under the slab, venting, PEX home runs from a manifold in the mech room |
| M-1 HVAC | Gas furnace FAU-1 in the attic over the back hall, A/C condenser AC-1 outside the mech room, gas piping from the meter, ducts and registers |
| Chat | Crew chat and open items, shared with the Zero Rd Firebase project in its own room (`waring-crew`) |

Each sheet links to a printable PDF packet in `packets/`.

## Hosting

Turn on GitHub Pages (Settings > Pages, deploy from `main`, root). The app works offline once loaded (`sw.js`).

## Editing

The page is generated. Change `build/plan.py` (walls, doors, windows, rooms, fixtures) or `build/trades.py` (circuits, devices, plumbing, HVAC), then:

```
python3 build/build.py             # rewrites index.html
python3 build/build.py --packets   # also reprints packets/*.pdf (needs Node with Playwright and Chromium)
```

Bump `VERSION` in `build/build.py` and in `sw.js` together so phones pick up the new copy.

Chat setup is in [CHAT-SETUP.md](CHAT-SETUP.md).
