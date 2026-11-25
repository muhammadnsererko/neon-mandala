import math
import time

import cv2
import numpy as np


WIDTH = 1040
HEIGHT = 780
WINDOW_NAME = "NEON | Mandala + Helix Turbine"
BACKGROUND = (8, 6, 17)


class NeonSimulation:
    def __init__(self):
        self.width = WIDTH
        self.height = HEIGHT
        self.center_x = self.width // 2
        self.center_y = self.height // 2
        self.scene = "flower"
        self.wind_speed = 7.5
        self.elapsed = 0.0
        self.paused = False
        self.last_tick = time.perf_counter()
        self.rng = np.random.default_rng(23)
        self.stars = np.column_stack((
            self.rng.random(100) * self.width,
            self.rng.random(100) * self.height,
            self.rng.uniform(0.5, 1.0, 100),
            self.rng.integers(1, 3, 100),
            self.rng.random(100) * math.tau,
        ))
        self.particle_angles = self.rng.uniform(0, math.tau, 100)
        self.particle_radii = self.rng.uniform(0.58, 1.2, 100)
        self.particle_speeds = self.rng.uniform(0.15, 0.8, 100) * self.rng.choice((-1, 1), 100)
        self.particle_sizes = self.rng.uniform(1.0, 2.8, 100)
        self.particle_phases = self.rng.uniform(0, math.tau, 100)
        self.background = self.make_background()
        self.image = None
        self.glow = None

    def make_background(self):
        y, x = np.mgrid[0:self.height, 0:self.width]
        dx = (x - self.center_x) / (self.width * 0.72)
        dy = (y - self.center_y) / (self.height * 0.76)
        vignette = np.clip(1.0 - 0.48 * np.sqrt(dx * dx + dy * dy), 0.2, 1.0)
        image = np.empty((self.height, self.width, 3), dtype=np.uint8)
        image[:, :, 0] = (BACKGROUND[0] + 13 * vignette).astype(np.uint8)
        image[:, :, 1] = (BACKGROUND[1] + 8 * vignette).astype(np.uint8)
        image[:, :, 2] = (BACKGROUND[2] + 4 * vignette).astype(np.uint8)
        return image

    def start_frame(self):
        self.image = self.background.copy()
        self.glow = np.zeros_like(self.image)
        for x, y, brightness, radius, phase in self.stars:
            pulse = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(self.elapsed * 1.5 + phase))
            value = int(100 * brightness * pulse)
            cv2.circle(self.image, (int(x), int(y)), int(radius), (value, value, value), -1, cv2.LINE_AA)

    def line(self, points, color, width=1, closed=False):
        vertices = np.asarray(points, dtype=np.int32).reshape((-1, 1, 2))
        if len(vertices) < 2:
            return
        glow_width = max(width * 5, 4)
        cv2.polylines(self.glow, [vertices], closed, color, glow_width, cv2.LINE_AA)
        cv2.polylines(self.image, [vertices], closed, color, width, cv2.LINE_AA)

    def polygon(self, points, fill, outline, width=2):
        vertices = np.asarray(points, dtype=np.int32).reshape((-1, 1, 2))
        if len(vertices) < 3:
            return
        cv2.fillPoly(self.image, [vertices], fill, cv2.LINE_AA)
        cv2.polylines(self.glow, [vertices], True, outline, max(width * 5, 5), cv2.LINE_AA)
        cv2.polylines(self.image, [vertices], True, outline, width, cv2.LINE_AA)

    def circle(self, center, radius, color, width=-1, glow=True):
        center = (int(center[0]), int(center[1]))
        radius = max(1, int(radius))
        if glow:
            thickness = max(3, radius // 2) if width < 0 else width * 5
            cv2.circle(self.glow, center, radius, color, thickness, cv2.LINE_AA)
        cv2.circle(self.image, center, radius, color, width, cv2.LINE_AA)

    def draw_title(self):
        title = "NEON / MANDALA" if self.scene == "flower" else "NEON / HELIX TURBINE"
        self.text(title, (26, 34), (215, 223, 242), 0.68, 2)
        self.text("T  SCENE     SPACE  PAUSE     R  RESET", (self.width - 26, 34), (126, 137, 173), 0.48, 1, right=True)
        self.text("NUMPY  /  OPENCV  /  POLAR GEOMETRY", (26, self.height - 22), (88, 104, 139), 0.43, 1)

    def text(self, value, position, color, scale, thickness, right=False, centered=False):
        font = cv2.FONT_HERSHEY_DUPLEX
        if right or centered:
            text_width = cv2.getTextSize(value, font, scale, thickness)[0][0]
            offset = text_width if right else text_width // 2
            position = (position[0] - offset, position[1])
        cv2.putText(self.image, value, position, font, scale, color, thickness, cv2.LINE_AA)

    def draw_particles(self):
        elapsed = self.elapsed
        spread = min(self.width, self.height) * 0.43
        angles = self.particle_angles + elapsed * self.particle_speeds
        radii = spread * self.particle_radii
        xs = self.center_x + np.cos(angles) * radii
        ys = self.center_y + np.sin(angles) * radii
        twinkles = 0.45 + 0.55 * np.sin(elapsed * 4.0 + self.particle_phases)
        colors = ((255, 248, 67), (218, 78, 255), (255, 121, 169), (255, 90, 255))
        for index in range(len(xs)):
            x, y = int(xs[index]), int(ys[index])
            radius = max(1, int(self.particle_sizes[index] * (0.7 + twinkles[index])))
            color = colors[index % len(colors)]
            self.circle((x, y), radius * 2, color, glow=True)
            cv2.circle(self.image, (x, y), radius, color, -1, cv2.LINE_AA)

    @staticmethod
    def petal_points(angle, length, half_width, progress, bend=0.0):
        t = np.linspace(0.0, progress, max(3, int(38 * progress)))
        width = half_width * np.power(np.maximum(np.sin(np.pi * t), 0.0), 0.78)
        forward = length * t
        sideways = bend * np.sin(np.pi * t)
        ca, sa = math.cos(angle), math.sin(angle)
        first = np.column_stack((ca * forward - sa * (sideways + width), sa * forward + ca * (sideways + width)))
        second = np.column_stack((ca * forward - sa * (sideways - width), sa * forward + ca * (sideways - width)))
        return np.vstack((first, second[::-1]))

    def draw_petal_layer(self, count, length, width, colors, progress, phase=0.0, bend=0.0):
        if progress <= 0:
            return
        total = progress * count
        for index in range(min(count, math.ceil(total))):
            petal_progress = min(1.0, total - index)
            angle = math.tau * index / count + phase
            points = self.petal_points(angle, length, width, petal_progress, bend)
            points += np.array([self.center_x, self.center_y])
            fill, outline, vein_color = colors
            self.polygon(points, fill, outline, 2)
            vein = self.petal_points(angle, length * 0.88, width * 0.08, petal_progress, bend)
            vein += np.array([self.center_x, self.center_y])
            self.line(vein, vein_color, 1)

    def draw_orbit(self, radius, color, phase, flatten=0.55):
        angles = np.linspace(0, math.tau, 220)
        points = np.column_stack((
            self.center_x + radius * np.cos(angles + phase),
            self.center_y + radius * flatten * np.sin(angles + phase),
        ))
        self.line(points, color, 1, closed=False)

    def draw_center(self):
        pulse = 1.0 + 0.08 * math.sin(self.elapsed * 3.2)
        for radius, color in ((42, (44, 18, 75)), (31, (91, 28, 149)), (22, (155, 55, 232)), (13, (220, 166, 255))):
            self.circle((self.center_x, self.center_y), radius * pulse, color, -1)
        self.circle((self.center_x, self.center_y), 7, (255, 250, 255), -1, glow=False)
        for index in range(12):
            angle = math.tau * index / 12 + self.elapsed * 0.24
            inner = 25 * pulse
            outer = 47 * pulse
            points = [
                (self.center_x + inner * math.cos(angle), self.center_y + inner * math.sin(angle)),
                (self.center_x + outer * math.cos(angle), self.center_y + outer * math.sin(angle)),
            ]
            self.line(points, (242, 192, 255), 1)

    def draw_flower(self):
        scale = min(self.width, self.height) * 0.001
        elapsed = self.elapsed
        self.draw_petal_layer(16, 236 * scale, 38 * scale,
                              ((39, 19, 7), (159, 223, 24), (236, 251, 169)),
                              min(1.0, elapsed / 2.8), phase=-math.pi / 2)
        self.draw_petal_layer(14, 190 * scale, 34 * scale,
                              ((53, 13, 23), (163, 51, 87), (255, 183, 228)),
                              max(0.0, min(1.0, (elapsed - 1.7) / 2.8)), phase=-math.pi / 2 + math.pi / 14, bend=4 * scale)
        self.draw_petal_layer(12, 145 * scale, 31 * scale,
                              ((52, 12, 54), (114, 29, 162), (236, 192, 255)),
                              max(0.0, min(1.0, (elapsed - 3.5) / 2.5)), phase=-math.pi / 2, bend=-3 * scale)
        self.draw_petal_layer(10, 99 * scale, 23 * scale,
                              ((31, 16, 59), (73, 36, 182), (189, 255, 255)),
                              max(0.0, min(1.0, (elapsed - 5.0) / 1.8)), phase=-math.pi / 2 + math.pi / 10)
        if elapsed > 1.2:
            self.draw_orbit(82 * scale, (255, 223, 37), elapsed * 0.08)
        if elapsed > 3.0:
            self.draw_orbit(119 * scale, (218, 103, 167), -elapsed * 0.05)
        if elapsed > 5.5:
            self.draw_orbit(157 * scale, (255, 83, 255), elapsed * 0.035)
        if elapsed > 6.3:
            self.draw_center()

    def draw_wind(self, wind):
        spacing = max(34, self.height // 15)
        for index in range(24):
            x = (index * 137 - self.elapsed * (95 + wind * 11)) % (self.width + 180) - 90
            y = (index * spacing * 1.73 + 78) % (self.height - 150) + 60
            length = 20 + wind * 2.1
            shade = 0.2 + 0.2 * (0.5 + 0.5 * math.sin(self.elapsed * 2 + index))
            color = (int(220 * shade), int(225 * shade), int(52 * shade))
            self.line(((x, y), (x - length, y)), color, 1)

    def project_rotor_point(self, fraction, angle, radius, rotor_center_y, rotor_height):
        depth = math.sin(angle)
        return (
            self.center_x + radius * math.cos(angle),
            rotor_center_y + fraction * rotor_height - depth * radius * 0.34,
            depth,
        )

    def draw_turbine(self):
        scale = min(self.width, self.height) * 0.001
        radius = 132 * scale
        rotor_height = 322 * scale
        rotor_center_y = self.center_y + 4 * scale
        wind = self.wind_speed + 0.8 * math.sin(self.elapsed * 0.7)
        angular_speed = 0.18 + wind * 0.12
        rotor_angle = self.elapsed * (0.18 + self.wind_speed * 0.12) + (0.8 * 0.12 / 0.7) * (1 - math.cos(self.elapsed * 0.7))
        self.draw_wind(wind)

        angles = np.linspace(0, math.tau, 180)
        ellipse = np.column_stack((
            self.center_x + radius * 1.38 * np.cos(angles),
            rotor_center_y + rotor_height * 0.56 * np.sin(angles),
        ))
        self.line(ellipse, (58, 45, 28), 2)

        panels = []
        sections = 42
        half_angle = 0.39
        for blade in range(3):
            blade_phase = math.tau * blade / 3
            for section in range(sections):
                y0 = section / sections - 0.5
                y1 = (section + 1) / sections - 0.5
                angle0 = rotor_angle + (y0 + 0.5) * math.tau * 1.15 + blade_phase
                angle1 = rotor_angle + (y1 + 0.5) * math.tau * 1.15 + blade_phase
                corners = [
                    self.project_rotor_point(y0, angle0 - half_angle, radius, rotor_center_y, rotor_height),
                    self.project_rotor_point(y0, angle0 + half_angle, radius, rotor_center_y, rotor_height),
                    self.project_rotor_point(y1, angle1 + half_angle, radius, rotor_center_y, rotor_height),
                    self.project_rotor_point(y1, angle1 - half_angle, radius, rotor_center_y, rotor_height),
                ]
                depth = sum(point[2] for point in corners) / len(corners)
                panels.append((depth, corners))

        for depth, corners in sorted(panels, key=lambda panel: panel[0]):
            polygon = [(x, y) for x, y, _ in corners]
            brightness = (depth + 1) * 0.5
            fill = (int(35 + 20 * brightness), int(52 + 105 * brightness), int(15 + 50 * brightness))
            edge = (int(155 + 95 * brightness), int(110 + 125 * brightness), int(30 + 70 * brightness))
            self.polygon(polygon, fill, edge, 2)

        shaft_top = rotor_center_y - rotor_height * 0.57
        shaft_bottom = rotor_center_y + rotor_height * 0.57
        self.line(((self.center_x, shaft_top), (self.center_x, shaft_bottom)), (112, 78, 24), 12)
        self.line(((self.center_x, shaft_top), (self.center_x, shaft_bottom)), (222, 243, 70), 3)
        for y in (shaft_top, shaft_bottom):
            self.circle((self.center_x, y), 8 * scale, (245, 255, 196), -1)
        self.circle((self.center_x, rotor_center_y), 15 * scale, (225, 255, 174), -1)
        self.circle((self.center_x, rotor_center_y), 4 * scale, (255, 255, 255), -1, glow=False)

        rpm = angular_speed * 60 / math.tau
        self.text(f"WIND  {wind:0.1f} m/s", (self.center_x, self.height - 72), (112, 255, 232), 0.58, 2, centered=True)
        self.text(f"ROTOR  {rpm:0.1f} RPM", (self.center_x, self.height - 42), (165, 183, 222), 0.48, 1, centered=True)
        self.text("UP / DOWN  WIND", (self.center_x, self.height - 20), (98, 116, 154), 0.4, 1, centered=True)

    def render(self):
        self.start_frame()
        if self.scene == "flower":
            self.draw_particles()
            self.draw_flower()
        else:
            self.draw_turbine()
        bloom = cv2.GaussianBlur(self.glow, (0, 0), sigmaX=12, sigmaY=12)
        self.image = cv2.addWeighted(self.image, 1.0, bloom, 0.82, 0)
        self.image = cv2.addWeighted(self.image, 1.0, self.glow, 0.38, 0)
        self.draw_title()
        return self.image

    def handle_key(self, key):
        if key in (27, ord("q"), ord("Q")):
            return False
        if key in (ord("t"), ord("T")):
            self.scene = "turbine" if self.scene == "flower" else "flower"
        elif key == ord(" "):
            self.paused = not self.paused
        elif key in (ord("r"), ord("R")):
            self.elapsed = 0.0
            self.paused = False
        elif key in (82, 2490368, ord("+"), ord("=")):
            self.wind_speed = min(15.0, self.wind_speed + 0.5)
        elif key in (84, 2621440, ord("-"), ord("_")):
            self.wind_speed = max(1.0, self.wind_speed - 0.5)
        return True

    def run(self):
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(WINDOW_NAME, WIDTH, HEIGHT)
        running = True
        try:
            while running:
                now = time.perf_counter()
                delta = min(now - self.last_tick, 0.05)
                self.last_tick = now
                if not self.paused:
                    self.elapsed += delta
                cv2.imshow(WINDOW_NAME, self.render())
                running = self.handle_key(cv2.waitKeyEx(16))
                try:
                    running = running and cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) >= 1
                except cv2.error:
                    running = False
        finally:
            cv2.destroyAllWindows()


def main():
    NeonSimulation().run()


if __name__ == "__main__":
    main()
