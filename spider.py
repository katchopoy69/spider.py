import tkinter as tk
import math
import random

W, H = 900, 600
REACH = 95          # how far the feet rest from the body
SEG = 65            # length of each leg segment
STEP_FRAMES = 8     # how fast a leg steps

root = tk.Tk()
root.title("Spider")
canvas = tk.Canvas(root, width=W, height=H, bg="#14141e", highlightthickness=0)
canvas.pack()

mouse = {"x": W / 2, "y": H / 2}


def on_move(event):
    mouse["x"], mouse["y"] = event.x, event.y


canvas.bind("<Motion>", on_move)

# Spider state
body = {"x": W / 2, "y": H / 2, "heading": 0.0, "vx": 0.0, "vy": 0.0, "glow": 0.0}

BG = (20, 20, 30)
WHITE = (255, 255, 255)

frame = {"n": 0}
sparkles = []   # white dots that float away from the spider and fade out
YELLOW = (255, 220, 40)


def blend(c1, c2, t):
    """Mix two RGB colors (t=0 gives c1, t=1 gives c2) and return a hex string."""
    t = max(0, min(1, t))
    r, g, b = (int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"


class Leg:
    def __init__(self, angle, group):
        self.angle = math.radians(angle)   # angle relative to the body direction
        self.group = group                 # legs in the same group step together
        self.foot = self.rest()
        self.stepping = False
        self.t = 0
        self.start = self.foot
        self.end = self.foot

    def rest(self):
        a = body["heading"] + self.angle
        return (body["x"] + math.cos(a) * REACH,
                body["y"] + math.sin(a) * REACH)


# 4 legs on each side, alternating groups so the spider walks naturally
legs = []
for i, ang in enumerate([-55, -25, 15, 50]):
    legs.append(Leg(ang, i % 2))          # one side
    legs.append(Leg(180 - ang, (i + 1) % 2))  # other side


def leg_joints(hip, foot):
    """Two-segment leg: returns the knee position."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = math.hypot(dx, dy) or 1
    d = min(d, 2 * SEG - 1)
    half = d / 2
    h = math.sqrt(max(SEG ** 2 - half ** 2, 0))
    mx, my = hip[0] + dx / 2, hip[1] + dy / 2
    nx, ny = -dy / math.hypot(dx, dy or 1), dx / math.hypot(dx, dy or 1)
    k1 = (mx + nx * h, my + ny * h)
    k2 = (mx - nx * h, my - ny * h)
    return k1 if k1[1] < k2[1] else k2   # knee bends upward


def update():
    # Move the body toward the mouse
    dx, dy = mouse["x"] - body["x"], mouse["y"] - body["y"]
    dist = math.hypot(dx, dy)
    if dist > 40:
        speed = min(6, dist * 0.06)
        body["vx"], body["vy"] = dx / dist * speed, dy / dist * speed
        # Turn smoothly to face the mouse
        target = math.atan2(dy, dx)
        diff = (target - body["heading"] + math.pi) % (2 * math.pi) - math.pi
        body["heading"] += diff * 0.12
    else:
        body["vx"] *= 0.8
        body["vy"] *= 0.8
    body["x"] += body["vx"]
    body["y"] += body["vy"]

    # Glow turns on while walking and fades out when he stops
    walking = math.hypot(body["vx"], body["vy"]) > 0.5
    target_glow = 1.0 if walking else 0.0
    body["glow"] += (target_glow - body["glow"]) * 0.25

    frame["n"] += 1

    # White sparkles are born around the spider while he walks, then drift and fade
    if body["glow"] > 0.3 and frame["n"] % 2 == 0:
        a = random.uniform(0, 2 * math.pi)
        r = random.uniform(10, 40)
        sparkles.append({
            "x": body["x"] + math.cos(a) * r,
            "y": body["y"] + math.sin(a) * r,
            "vx": random.uniform(-0.8, 0.8) - body["vx"] * 0.2,
            "vy": random.uniform(-1.2, 0.2) - body["vy"] * 0.2,
            "life": 1.0,
            "size": random.uniform(1.5, 3.5),
        })
    for sp in sparkles:
        sp["x"] += sp["vx"]
        sp["y"] += sp["vy"]
        sp["life"] -= 0.02
    sparkles[:] = [sp for sp in sparkles if sp["life"] > 0]

    # Update legs
    for leg in legs:
        if leg.stepping:
            leg.t += 1 / STEP_FRAMES
            t = min(leg.t, 1)
            leg.foot = (leg.start[0] + (leg.end[0] - leg.start[0]) * t,
                        leg.start[1] + (leg.end[1] - leg.start[1]) * t)
            if t >= 1:
                leg.stepping = False
        else:
            rest = leg.rest()
            far = math.hypot(leg.foot[0] - rest[0], leg.foot[1] - rest[1])
            other_busy = any(l.stepping for l in legs if l.group != leg.group)
            if far > REACH * 0.5 and not other_busy:
                leg.stepping = True
                leg.t = 0
                leg.start = leg.foot
                leg.end = (rest[0] + body["vx"] * 6, rest[1] + body["vy"] * 6)

    draw()
    root.after(16, update)


def draw():
    canvas.delete("all")
    bx, by, h = body["x"], body["y"], body["heading"]
    glow = body["glow"]

    # Yellow halo behind the spider (outer rings are faint, inner rings brighter)
    if glow > 0.02:
        rings = 12
        for i in range(rings):
            wave = 1 + 0.12 * math.sin(frame["n"] * 0.25 - i * 0.5)   # ripple moving outward
            radius = (110 - i * 7) * wave
            strength = (i + 1) / rings * 0.9 * glow
            canvas.create_oval(bx - radius, by - radius, bx + radius, by + radius,
                               fill=blend(BG, YELLOW, strength), outline="")

    # Floating white sparkles (they fade into the background)
    for sp in sparkles:
        c = blend(BG, WHITE, sp["life"])
        z = sp["size"] * (0.5 + sp["life"] / 2)
        canvas.create_oval(sp["x"] - z, sp["y"] - z, sp["x"] + z, sp["y"] + z, fill=c, outline="")

    # Legs
    for leg in legs:
        a = h + leg.angle
        hip = (bx + math.cos(a) * 12, by + math.sin(a) * 12)
        knee = leg_joints(hip, leg.foot)
        canvas.create_line(hip, knee, leg.foot, fill="#c8c8d8",
                           width=4, capstyle="round", joinstyle="round")

    # Abdomen (behind) and head (front)
    ax, ay = bx - math.cos(h) * 22, by - math.sin(h) * 22
    outline = blend((200, 200, 216), YELLOW, glow)
    abdomen_fill = blend((43, 43, 58), (190, 150, 20), glow)
    head_fill = blend((58, 58, 77), (220, 180, 30), glow)
    canvas.create_oval(ax - 24, ay - 24, ax + 24, ay + 24, fill=abdomen_fill, outline=outline, width=2)
    hx, hy = bx + math.cos(h) * 14, by + math.sin(h) * 14
    canvas.create_oval(hx - 15, hy - 15, hx + 15, hy + 15, fill=head_fill, outline=outline, width=2)

    # Eyes
    for side in (-0.5, 0.5):
        ex = hx + math.cos(h + side) * 10
        ey = hy + math.sin(h + side) * 10
        canvas.create_oval(ex - 3, ey - 3, ex + 3, ey + 3, fill="red", outline="")

    if glow > 0.05:
        # A bright yellow light that slides back and forth along his body
        pos = (math.sin(frame["n"] * 0.15) + 1) / 2
        lx = ax + (hx - ax) * pos
        ly = ay + (hy - ay) * pos
        for r, t in ((22, 0.35), (15, 0.6), (8, 0.9)):
            canvas.create_oval(lx - r, ly - r, lx + r, ly + r,
                               fill=blend((220, 180, 30), (255, 255, 160), t * glow), outline="")

        # White dots orbiting around him
        for i in range(10):
            ang = frame["n"] * 0.07 + i * (2 * math.pi / 10)
            rad = 50 + 12 * math.sin(frame["n"] * 0.1 + i)
            ox = bx + math.cos(ang) * rad
            oy = by + math.sin(ang) * rad
            z = 2 + (i % 3)
            canvas.create_oval(ox - z, oy - z, ox + z, oy + z,
                               fill=blend(BG, WHITE, glow), outline="")


update()
root.mainloop()
