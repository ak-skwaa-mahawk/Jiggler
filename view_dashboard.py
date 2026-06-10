import re
import time
import curses
import os

LOG_FILE = "manifold_grpc.log"

# Strict regex to extract variables from the Rust core log string
# GS[BAND=GOLDILOCKS  | S=0.985 | Curv=1.408 | Target=1.400 | Belt=90.612 | Throat=21.821]
PARSER = re.compile(
    r"GS\[BAND=(?P<band>\w+)\s*\|\s*S=(?P<s>[\d\.]+)\s*\|\s*Curv=(?P<curv>[\d\.]+)\s*\|\s*Target=(?P<target>[\d\.]+)\s*\|\s*Belt=(?P<belt>[\d\.]+)\s*\|\s*Throat=(?P<throat>[\d\.]+)\]"
)

def follow_log():
    """Generator that checks for fresh log lines at the end of the file descriptor."""
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("══════════════════════════════════════════════════════════════\n")
    
    with open(LOG_FILE, "r") as f:
        # Catch up straight to the current end of file footprint
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def draw_tui(stdscr):
    # Initialize terminal colors and layout settings
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    
    # Define cohesive state color assignments
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Goldilocks
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)   # Deep GS
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK) # Marginal
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)    # Subcritical
    curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Default Borders

    stdscr.clear()
    stdscr.refresh()

    stdscr.addstr(0, 0, "🌀 [TORDIAL-GS] Sovereign Manifold Telemetry Matrix View Active", curses.color_pair(5) | curses.A_BOLD)
    stdscr.addstr(1, 0, "Monitoring background gRPC log channels... Press 'q' to quit.", curses.color_pair(5) | curses.A_DIM)
    stdscr.refresh()

    for line in follow_log():
        # Watch for keyboard quit triggers
        try:
            key = stdscr.getch()
            if key == ord('q'):
                break
        except Exception:
            pass

        match = PARSER.search(line)
        if match:
            data = match.groupdict()
            band = data['band']
            score = float(data['s'])
            curv = float(data['curv'])
            target = float(data['target'])
            belt = float(data['belt'])
            throat = float(data['throat'])
            delta = curv - target

            # Choose context color pair based on state band tracking
            if "GOLDILOCKS" in band:
                c_pair = curses.color_pair(1)
            elif "DEEP_GS" in band:
                c_pair = curses.color_pair(2)
            elif "MARGINAL" in band:
                c_pair = curses.color_pair(3)
            else:
                c_pair = curses.color_pair(4)

            # Redraw structured viewport cards inside the terminal buffer
            stdscr.addstr(3, 0, "┌──────────────────────────────────────────────────────────────┐", curses.color_pair(5))
            stdscr.addstr(4, 0, "│ GS REGULATOR STATUS STATE: [               ]                 │", curses.color_pair(5))
            stdscr.addstr(4, 30, f"{band:<13}", c_pair | curses.A_BOLD)
            stdscr.addstr(4, 48, f"Score: {score:.3f}", curses.color_pair(5))
            
            stdscr.addstr(5, 0, "├──────────────────────────────────────────────────────────────┤", curses.color_pair(5))
            stdscr.addstr(6, 0, "│ Curvature Topology Deviation:                                │", curses.color_pair(5))
            stdscr.addstr(7, 0, "│   Target [       ]  ───  Live [       ]                      │", curses.color_pair(5))
            stdscr.addstr(7, 12, f"{target:.3f}", curses.color_pair(5))
            stdscr.addstr(7, 33, f"{curv:.3f}", c_pair | curses.A_BOLD)
            stdscr.addstr(7, 43, f"(Δ {delta:+.4f})", c_pair)

            stdscr.addstr(8, 0, "├──────────────────────────────────────────────────────────────┤", curses.color_pair(5))
            stdscr.addstr(9, 0, "│ Physical Substrate Actuators Geometry Parameters:            │", curses.color_pair(5))
            stdscr.addstr(10, 0, "│   Throat Radius:           mm  │  Belt Tension:            N │", curses.color_pair(5))
            stdscr.addstr(10, 19, f"{throat:.3f}", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(10, 50, f"{belt:.3f}", curses.color_pair(2) | curses.A_BOLD)
            stdscr.addstr(11, 0, "└──────────────────────────────────────────────────────────────┘", curses.color_pair(5))
            
            stdscr.refresh()

if __name__ == '__main__':
    try:
        curses.wrapper(draw_tui)
    except KeyboardInterrupt:
        pass
    print("\n🛰️  Dashboard safely unhooked from log files. Core intact.")
