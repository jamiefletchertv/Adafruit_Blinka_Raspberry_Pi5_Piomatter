// Custom orientation mapping for panel layout: [3][2][1] / [4][5][6]
// This maps logical coordinates to physical panel positions

inline int custom_panel_orientation(int width, int height, int x, int y) {
    // For a 192x64 display (3x2 panels of 64x32 each)
    // Current logical layout: [1][2][3] / [4][5][6]
    // Physical layout:        [3][2][1] / [4][5][6]
    
    // Determine which panel this coordinate is in
    int panel_x = x / 64;  // 0, 1, or 2
    int panel_y = y / 32;  // 0 or 1
    int local_x = x % 64;  // position within panel
    int local_y = y % 32;  // position within panel
    
    // Remap top row panels: logical [0][1][2] -> physical [2][1][0]
    if (panel_y == 0) {
        panel_x = 2 - panel_x;  // Flip the x ordering for top row
    }
    // Bottom row stays the same: [0][1][2] -> [0][1][2]
    
    // Convert back to global coordinates
    int new_x = panel_x * 64 + local_x;
    int new_y = panel_y * 32 + local_y;
    
    return new_x + width * new_y;
}