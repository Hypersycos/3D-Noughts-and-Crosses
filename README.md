# 3D-Noughts-and-Crosses

An implementation of 3D Naughts and Crosses in pygame.
I highly recommend more than 2 players, as otherwise it's quite easy for P1 to force a win.

Binds can be customised by changing the dictionary at the top of ./3dNaughtsAndCrosses.py

Defaults:
* Move Selection
  * W: Forwards
  * A: Left
  * S: Backwards
  * D: Right
  * Q: Down
  * E: Up
* Space:
  * Take turn
  * Start match
  * Return to menu after victory
* Zoom
  * 3D
    * Mousewheel up: Zooms in
    * Mousewheel down: Zooms out
  * 2D
    * Mousewheel up: Decreases number of visible grids
    * Mousewheel down: Increases number of visible grids
* C: Swap between 2D and 3D views
* H: Toggle visibility of selection - must be visible to take turn.

3D view only:
* Drag LMB: Rotate Camera
* Drag RMB: Move Camera Focus (ala arrow keys)
* T: Toggle cube fill
* \-: Decrease explosion
* +: Increase explosion
* F: Swap camera focus from centre and selection
* Rotate Camera
  * Arrow Keys: Rotates around focus point
  * Arrow Keys: Acts like FPS camera when fully zoomed in
* R: Reset Camera
* Move Camera
  * I: Forwards
  * K: Backwards
  * J: Left
  * L: Right
  * U: Down
  * O: Up

Potential todo list:
* Modify line length
* Loading/Saving
* Rebinding menu
* Add another LoD level (or find some way of making it run better)