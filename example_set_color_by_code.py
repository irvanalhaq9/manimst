from manimlib import *

class TestFunc(InteractiveScene):
    def construct(self):
        
        n = 10
        points = np.random.uniform(-10,10,(n,3))
        dots = DotCloud(points,radius=0.3,glow_factor=2)
        # Buat array warna acak (RGB) untuk setiap titik
        colors = np.random.uniform(0, 1, (n, 3))  # Random RGB
        rgba = np.hstack((colors, np.ones((n, 1))))  # Tambah alpha (1 untuk opaque)
        # Terapkan warna acak ke dots
        dots.set_rgba_array(rgba)
        
        # Atur radius acak untuk setiap titik antara 0.01 dan 3
        random_radii = np.random.uniform(0.01, 2, (n, 1))
        dots.data['radius'][:] = random_radii
        
        # dots.set_color_by_gradient(RED, GREEN, BLUE)
        self.play(FadeIn(dots))
        
        
        n1 = 10
        points1 = np.random.uniform(-10,10,(n1,3))
        dots1 = DotCloud(points1,radius=0.3)
        dots1.set_color_by_gradient(RED, GREEN, BLUE)
        self.play(FadeIn(dots1))
        
        dot = GlowDot()
        # tanpa shading, .set_color_by_code() tidak bekerja
        dot.set_shading(0,0.1,0)
        # Kode GLSL untuk warna merah
        glsl_code = """
        color.rgb = vec3(1.0, 0.0, 0.0);
        """
        
        dot.set_color_by_code(glsl_code)
        self.add(dot)
        
        # Buat titik-titik acak
        n2 = 10
        points2 = np.random.uniform(-10, 10, (n2, 3))
        dots2 = DotCloud(points2)
        
        # Atur radius acak untuk setiap titik antara 0.01 dan 3
        random_radii = np.random.uniform(0.01, 1, n2)
        dots2.set_radii(random_radii)
        
        # Atur shading agar finalize_color dipanggil
        dots2.set_shading(0.0, 0.1, 0.0)  # gloss=1, reflectiveness=0, shadow=0
        
        # Kode GLSL untuk warna acak berdasarkan posisi
        glsl_code2 = """
        float rand = fract(sin(dot(point, vec3(12.9898, 78.233, 45.5432))) * 43758.5453);
        color = vec4(
            fract(rand),
            fract(rand * 1.618033988749895),
            fract(rand * 3.141592653589793),
            1.0
        );
        """
        
        # Terapkan warna menggunakan set_color_by_code
        dots2.set_color_by_code(glsl_code2)
        
        self.play(FadeIn(dots2))
        self.embed()

        
        