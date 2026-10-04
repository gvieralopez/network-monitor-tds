# Device drawings replace icons

Each device card shows a drawing of the kind of device it is, on top of the artwork generated from its MAC address. The drawings replaced a set of line icons. They are SVG symbols written by hand to one spec ([Designing device drawings](../device-drawings.md)), kept in one sprite that every page includes inline, with gradients shared between them. Every category has a default drawing; any other drawing is the user's choice in the device panel, and none is ever picked automatically from a vendor or hostname.

Product images were considered and rejected. The monitor rarely knows the exact model, so an image of a specific product would often be wrong, and product photos or logos would bring copyright and trademark problems into the repository. Drawings of kinds of devices avoid both, stay small enough to review in a diff, and look like one family because they share a canvas, a camera angle, light and materials.

## Consequences

- Drawings show a kind of device ("tower console, white"), never a product: no brand names in ids or labels, and no logos or signature product details in the drawings.
- A drawing's id is stored in the user's labels, so an id is never renamed or removed. The names of the old line icons were kept for that reason.
- Every id in the sprite must be unique on the page, so symbols contain no ids of their own and use only the shared gradients.
- The sprite is inline rather than an external file because gradients referenced through an external `<use>` have been unreliable across browsers. It adds about 20 KB to each page.
- Cards come in two styles, chosen per browser like the theme: Artwork, with the drawing on the generated pattern, and Studio, on a plain backdrop tinted by the category with a contact shadow sized from the drawing's footprint. Neither style is drawn into the drawings, so new drawings work in both.
- Tests check the sprite against the registry and the spec's mechanical rules; how a drawing looks is checked by eye, in the app.
