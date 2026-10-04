# Designing device drawings

Every device card shows a drawing of the kind of device it is. This page is the spec for adding one. Follow it exactly: the set looks like one family only because every drawing obeys the same canvas, camera, light and materials.

A drawing shows **what kind of device** something is ("a tower console, white"), never **which product** it is. Users name their devices; the drawing only has to be recognisable.

## Where drawings live

- `src/network_monitor_tds/web/templates/drawings.svg`: one `<symbol>` per drawing, plus the shared gradients they fill with and the blur filter for the Studio card style's contact shadow. It is included once, inline, in every page.
- `src/network_monitor_tds/web/drawings.py`: the registry. Each drawing has an id, a label, the category it is listed under in the picker, and a footprint. Each category names its default drawing.

Adding a drawing means adding a symbol and a registry entry. Nothing else changes.

## Canvas and camera

| Rule | Value |
|---|---|
| Symbol | `<symbol id="dv-{id}" viewBox="0 0 200 140">` |
| Safe area | x 16–184, y 6–112. Nothing is drawn outside it. |
| Ground line | y = 112. The object stands on it: its lowest point is at 110–112. |
| Size | Fill the safe area in the object's longest direction. A TV is 168 wide; a phone is 102 tall. |
| Camera | Front view from slightly above. |
| Box tops | A band at most 14 units deep above the front face, e.g. `M36 82l14-12h100l14 12z`. |
| Round tops | An ellipse with ry ≈ 0.3 × rx. |
| Light | From the upper left. Gradients run light at the top or left to dark at the bottom or right. |

Things that are normally seen from the front (TVs, monitors, consoles) show no top. Things only recognisable from another side are drawn from that side: phones from the back, so their colour and camera show.

Keep proportions true to the real object. Don't stretch a drawing to fill the safe area: a controller is about 1.75 times as wide as it is tall, not 2.5.

## Materials

Fill large surfaces only with these shared gradients. Never define a gradient inside a symbol.

| Id | Use | Stops |
|---|---|---|
| `dv-dark` | Dark plastic, bezels | `#474d57` → `#1b1e23`, vertical |
| `dv-dark-h` | Dark cylinders | `#1d2025`, `#4a5059` at 35%, `#1d2025`, horizontal |
| `dv-white` | White plastic | `#fbfcfd` → `#c3c8cf`, vertical |
| `dv-white-h` | White cylinders | `#b9bec5`, `#f7f8fa` at 35%, `#bfc4cb`, horizontal |
| `dv-alu` | Aluminium | `#e3e7eb` → `#a9afb7`, vertical |
| `dv-glass` | Screen, switched off | `#34507a` → `#121826`, diagonal |
| `dv-wall` | Screen showing a wallpaper | `#2d4a7a`, `#6a3d78` at 55%, `#d07a5c`, diagonal |
| `dv-fabric-h` | Fabric cylinders, with the `dv-fabric` dot pattern on top | `#5a5f66`, `#a3a9b0` at 35%, `#62676e`, horizontal |
| `dv-blue` | Coloured part, blue | `#7fa2c9` → `#4b6d96`, vertical |
| `dv-coral` | Coloured part, coral | `#ea9a8b` → `#bc6457`, vertical |
| `dv-gray` | Coloured part, grey | `#a7adb5` → `#6b7178`, vertical |
| `dv-kraft` | Cardboard | `#d6ad76` → `#ac8250`, vertical |
| `dv-bulb-glass` | Lit glass | radial `#fffaf0`, `#fbe3ad` at 60%, `#eec375` |

Small details use these flat colours:

| Colour | Use |
|---|---|
| `#262a31` | Buttons, recesses, sticks |
| `#3b414b` | Tops of sticks and knobs |
| `#2a2e35` | Bays, ports, side bands |
| `#0b0d10` | The darkest openings: lenses, vents |
| `#5a606a`, `#2e333a` | Top faces of dark boxes |
| `#fbfcfd`, `#eef0f3` | Top faces and insets of white objects |
| `#3ccf8e`, `#f0b44a`, `#7fd3ff` | Status lights only: green, amber, blue |

Other flat colours are allowed only as a shade of the material they sit on, such as a bezel a little darker than `dv-dark` or tape a little darker than `dv-kraft`, or as a wallpaper detail on a `dv-wall` screen. Never introduce a new hue.

A new shared gradient is allowed only when an existing one can't represent the material and at least two drawings will use it. Add it to this table in the same change.

## Construction

- Fills, not outlines. Strokes are only for vents, seams, rings and filaments, 1.4–1.6 wide with round caps.
- Glass gets one diagonal glare: a white shape at 5–7% opacity across the upper-left part of the screen.
- Keep it simple: about a dozen elements, counting a group of repeated parts as one. The drawing is shown 130 px wide on a card and about 95 px in the picker: a detail smaller than 3 units disappears.
- Group repeated small parts (`<g fill="#262a31">…</g>`) instead of repeating the fill.
- Use `translate` on a group to sit an object on the ground line; don't use `scale`.
- No `id` attributes inside a symbol: every id on the page must be unique, and a clash makes a drawing disappear silently.

Never draw:

- text, numbers, logos or brand marks, except the question mark on the unknown device's box;
- a product's signature detail, the one thing that identifies that exact model. Draw the shape family, not the model;
- shadows, reflections on the floor, or backgrounds. The card style draws those;
- new hues outside the materials above.

## Names and registry entries

- The id is lowercase kebab case: object, then form, then colour. For example `console-hybrid-gray`, `phone-white` or `console-tower-black`. No brand or model names.
- The label is short plain English describing form and colour, in the same order: "Hybrid console, grey". No brand or model names here either.
- The category is where the drawing appears in the picker. It does not change the device's category.
- The footprint is the half-width of the object's base, in canvas units. Studio cards draw the contact shadow from it. Measure it: a 56-unit-wide base has a footprint of 28.
- Never rename or remove an id. Users' saved labels refer to them.

## Worked example: the controller

```svg
<symbol id="dv-gamepad" viewBox="0 0 200 140">
  <path d="M72 44h56c14 0 22 8 25 20l6 32c2 10-7 18-15 12l-13-12H69l-13 12c-8 6-17-2-15-12l6-32c3-12 11-20 25-20z" fill="url(#dv-dark)"/>
  <path d="M72 44h56c8 0 14 3 18 8H54c4-5 10-8 18-8z" fill="#fff" opacity=".08"/>
  <g fill="#262a31"><rect x="60" y="61.5" width="16" height="5" rx="1.5"/><rect x="65.5" y="56" width="5" height="16" rx="1.5"/><circle cx="132" cy="58" r="2.8"/><circle cx="132" cy="70" r="2.8"/><circle cx="126" cy="64" r="2.8"/><circle cx="138" cy="64" r="2.8"/></g>
  <circle cx="86" cy="81" r="8" fill="#262a31"/><circle cx="86" cy="81" r="5" fill="#3b414b"/>
  <circle cx="114" cy="81" r="8" fill="#262a31"/><circle cx="114" cy="81" r="5" fill="#3b414b"/>
  <rect x="92" y="50" width="16" height="3" rx="1.5" fill="#7fd3ff" opacity=".85"/>
</symbol>
```

- The body is one path in `dv-dark`, 118 wide and 67 tall, with its grips ending on the ground line.
- A white band at 8% opacity along the top edge catches the light from above.
- The d-pad and face buttons are grouped in the recess colour, and the sticks are two circles each.
- A blue status light is the one accent.
- Registry entry: id `gamepad`, label "Controller", category gaming, footprint 59 (its grips span x 41–159).

## Checking a new drawing

Run the app with the demo plugin, open a device, pick the new drawing and check:

1. It sits on the ground line and stays clear of the status pill (top left), the NEW badge (top right) and the IP address (bottom right).
2. It reads at the picker's tile size, and the closest existing variant can still be told apart from it.
3. It looks right in both card styles (Artwork and Studio) and both themes.
4. It still reads when the device is offline and its card is desaturated.
5. Next to its neighbours in the picker, the camera angle, light and size look like one family.

## Asking an agent to add drawings

> Add device drawings for: {list of devices}. Follow `docs/device-drawings.md` exactly: use the existing canvas, camera, shared materials and naming, add a symbol to `drawings.svg` and an entry to the registry in `drawings.py` for each, and use the controller example as the reference for level of detail. Draw the device family, not a specific product. Report each new id, label, category and footprint.
