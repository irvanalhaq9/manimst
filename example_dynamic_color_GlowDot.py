from manimlib import *

class TestFunc(InteractiveScene):
    def construct(self):
        n = 100
        points = np.random.uniform(-10,10,(n,3))
        dots = DotCloud(points,radius=0.3,glow_factor=0)
        # Buat array warna acak (RGB) untuk setiap titik
        colors = np.random.uniform(0, 1, (n, 3))  # Random RGB
        rgba = np.hstack((colors, np.ones((n, 1))))  # Tambah alpha (1 untuk opaque)
        # Terapkan warna acak ke dots
        dots.set_rgba_array(rgba)
        self.play(FadeIn(dots))
        self.wait(2)
        random_radii = np.random.uniform(0.05, 1, n)
        self.play(dots.animate(run_time=10).set_radii(random_radii))
        self.play(dots.animate.set_glow_factor(2))
        self.play(dots.animate.set_quad_factor(1))
        self.play(dots.animate.set_dynamic_color(1))
        self.wait(5)
        self.play(dots.animate.set_dynamic_color(0))
        
        # self.play(dots.animate(run_time=2).set_blink_factor(1))
        self.wait(5)
        # self.embed()
        # self.play(dots.animate.set_shading(0,0.1,0))
        self.play(dots.animate(run_time=2).set_blink_factor(1))
        self.wait(10)
        self.play(dots.animate(run_time=2).set_blink_factor(0))
        self.wait(3)
        self.play(dots.animate(run_time=2).set_blink_factor(1))
        # set_dynamic_color tidak bekerja jika 
        # set_blink_factor 1
        self.play(dots.animate(run_time=2).set_dynamic_color(1))
        self.wait(10)
        self.embed()
        
        self.play(dots.animate(run_time=2).set_blink_factor(0.5))
        self.play(dots.animate(run_time=2).set_dynamic_color(0))
        dots.set_blink_type("saturation")
        self.wait(30)
        self.play(dots.animate(run_time=2).set_blink_factor(0))
        
        