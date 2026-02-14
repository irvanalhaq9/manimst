from manimlib import *

class GlowDotScene(InteractiveScene):
    
    def camera_position(self) -> float:
        return self.camera.uniforms["camera_position"]
        
    def emit_gl_Position(self,point: np.ndarray,**kwargs,) -> np.ndarray:
        gl_Position = self.camera.emit_gl_Position(point,**kwargs)
        return gl_Position
    
    def get_ndc_coordinate(self,point: np.ndarray,**kwargs) -> np.ndarray:
        """
        Ini adalah koordinat di layar yang sebenarnya. 
        Koordinat setelah penyesuaian perspektif 3 dimensi.
        """
        ndc = self.camera.get_ndc_coordinate(point, **kwargs)
        return ndc
    
    def get_ndc_for_manim(self, point: np.ndarray) -> np.ndarray:
        """
        Hanya ambil koordinat x dan y karena z hanya untuk depth test opengl
        """
        ndc = self.get_ndc_coordinate(point)
        x, y = ndc[0], ndc[1]
        return np.array([x, y, 0.0])  # set z = 0

    def ndc_to_manim(self, x: float, y: float) -> np.ndarray:
        """
        Konversi NDC ke koordinat manim agar bisa buat polygon
        setelah perspektif 3 dimensi. Ini panjang yang sebenarnya.
        Bisa saja nilainya berbeda
        dari nilai quad awal yang dimasukkan.
        """
        # NDC x ∈ [-1, 1] → Manim x ∈ [-7.1111, 7.1111]
        # NDC y ∈ [-1, 1] → Manim y ∈ [-4, 4]
        manim_x = x * (16 / 9) * 4
        manim_y = y * 4
        return np.array([manim_x, manim_y, 0.0])

class QuadPolygon(Polygon):
    
    def get_side_lengths(self) -> list[float]:
        vertices = list(self.get_vertices())
        vertices.append(vertices[0])  # pastikan sisi terakhir kembali ke awal
        return [
            np.linalg.norm(vertices[i + 1] - vertices[i])
            for i in range(len(vertices) - 1)
        ]


class QuadTest(GlowDotScene):
    def construct(self):
        quad = GlowDot(radius=1, color=PURE_BLUE)
        self.play(FadeIn(quad))
        # self.embed()
        self.play(quad.animate.set_quad_factor(0.5))
        self.play(quad.animate.set_quad_factor(1))
        self.play(quad.animate.set_glow_factor(0.5))
        self.play(quad.animate.set_glow_factor(1))
        self.play(quad.animate.set_glow_factor(0))
        # self.play(self.frame.animate.shift(LEFT*5))
        self.play(quad.animate.shift(UP*2.5))
        # self.play(quad.animate.shift(RIGHT*2.5))
        # self.play(quad.animate.rotate(30*DEG,axis=IN, about_point=ORIGIN))
        # self.play(quad.animate.rotate(30*DEG,axis=OUT, about_point=RIGHT))
        self.play(self.frame.animate.set_euler_angles(gamma=30*DEG))

        cam_pos = self.camera_position()
        coords = quad.get_quad_coordinates(cam_pos)

        # Ambil NDC dari semua titik
        ndc_points = [self.get_ndc_for_manim(p[0]) for p in coords]
        sorted_ndc = [
            ndc_points[3],  # kanan atas
            ndc_points[1],  # kiri atas
            ndc_points[0],  # kiri bawah
            ndc_points[2],  # kanan bawah
        ]
        # Konversi ke koordinat Manim
        manim_points = [self.ndc_to_manim(x, y) for x, y, _ in sorted_ndc]

        poly = QuadPolygon(*manim_points, color=YELLOW, stroke_width=2)
        # poly.shift(LEFT*5)
        poly.rotate(30*DEG,axis=OUT, about_point=self.frame.get_center())
        self.play(ShowCreation(poly))
        self.wait()
        poly_verts = poly.get_vertices()
        up_line = Line(poly_verts[0],poly_verts[1])
        up_line.set_color(RED)
        self.add(up_line)
        print(up_line.get_length())
        print(poly.get_side_lengths())
            # perhatikan hasilnya berbeda dengan panjang awal,
            # awalnya persegi dengan panjang sisi 2.
            # sekarang berbeda karena disesuaikan 
            # dengan perspektif 3 dimensi
        self.embed()
        self.play(self.frame.animate.increment_theta(10*DEG))
        # self.play(self.frame.animate.increment_theta(10*DEG))
        # self.play(quad.animate.rotate(30*DEG,axis=IN, about_point=ORIGIN))
        # self.play(quad.animate.rotate(30*DEG,axis=OUT, about_point=RIGHT))
        self.play(self.frame.animate.set_height(15))
        self.play(self.frame.animate.shift(DL*3))
        self.play(self.frame.animate.shift(LEFT*5))
        

class QuadTestTwo(GlowDotScene):
    def construct(self):
        plane = NumberPlane(
            x_range=(-16,16,1),
            y_range=(-8,8,1),
        )
        # plane.set_opacity(0.7)
        self.add(plane)
        quad = GlowDot(radius=1, color=PURE_BLUE)
        self.play(FadeIn(quad))
        # self.embed()
        self.play(quad.animate.set_quad_factor(0.5))
        self.play(quad.animate.set_quad_factor(1))
        self.play(quad.animate.set_glow_factor(0.5))
        self.play(quad.animate.set_glow_factor(1))
        self.play(quad.animate.set_glow_factor(0))
        
        self.play(quad.animate.shift(UP*2.5))
        self.play(quad.animate.shift(RIGHT*3))
        
    
        # self.play(self.frame.animate.set_euler_angles(gamma=30*DEG))

        self.play(self.frame.animate.shift(2*UP+LEFT))
        
        cam_pos = self.camera_position()
        coords = quad.get_quad_coordinates(cam_pos)

        # Ambil NDC dari semua titik
        ndc_points = [self.get_ndc_for_manim(p[0]) for p in coords]
        sorted_ndc = [
            ndc_points[3],  # kanan atas
            ndc_points[1],  # kiri atas
            ndc_points[0],  # kiri bawah
            ndc_points[2],  # kanan bawah
        ]
        # Konversi ke koordinat Manim
        manim_points = [self.ndc_to_manim(x, y) for x, y, _ in sorted_ndc]

        poly = QuadPolygon(*manim_points, color=YELLOW, stroke_width=2)

        # poly.rotate(30*DEG,axis=OUT, about_point=self.frame.get_center())

        self.play(ShowCreation(poly))
        self.wait()
        poly_verts = poly.get_vertices()
        up_line = Line(poly_verts[0],poly_verts[1])
        up_line.set_color(RED)
        self.add(up_line)
        print(up_line.get_length())
        print(poly.get_side_lengths())
            # perhatikan hasilnya berbeda dengan panjang awal,
            # awalnya persegi dengan panjang sisi 2.
            # sekarang berbeda karena disesuaikan 
            # dengan perspektif 3 dimensi
        # self.play(self.frame.animate.shift(2*DOWN+RIGHT))
        # self.play(self.frame.animate.shift(2*UP+LEFT))

        self.play(
            poly.animate.shift(UP*2+LEFT),
            up_line.animate.shift(UP*2+LEFT)
        )
        self.embed()


class QuadTestThree(GlowDotScene):
    def construct(self):
        plane = NumberPlane(
            x_range=(-16,16,1),
            y_range=(-8,8,1),
        )
        # plane.set_opacity(0.7)
        self.add(plane)
        quad = GlowDot(radius=1, color=PURE_BLUE)
        self.play(FadeIn(quad))
        # self.embed()
        self.play(quad.animate.set_quad_factor(0.5))
        self.play(quad.animate.set_quad_factor(1))
        self.play(quad.animate.set_glow_factor(0.5))
        self.play(quad.animate.set_glow_factor(1))
        self.play(quad.animate.set_glow_factor(0))
        
        self.play(quad.animate.shift(UP*2.5))
        self.play(quad.animate.shift(RIGHT*3))
        
        self.play(self.frame.animate.set_euler_angles(gamma=30*DEG))
        self.play(self.frame.animate.shift(2*UP+LEFT))
        
        cam_pos = self.camera_position()
        coords = quad.get_quad_coordinates(cam_pos)

        # Ambil NDC dari semua titik
        ndc_points = [self.get_ndc_for_manim(p[0]) for p in coords]
        sorted_ndc = [
            ndc_points[3],  # kanan atas
            ndc_points[1],  # kiri atas
            ndc_points[0],  # kiri bawah
            ndc_points[2],  # kanan bawah
        ]
        # Konversi ke koordinat Manim
        manim_points = [self.ndc_to_manim(x, y) for x, y, _ in sorted_ndc]

        poly = QuadPolygon(*manim_points, color=YELLOW, stroke_width=2)
        self.play(ShowCreation(poly))
        
        self.wait()
        poly_verts = poly.get_vertices()
        up_line = Line(poly_verts[0],poly_verts[1])
        up_line.set_color(RED)
        
        self.play(ShowCreation(up_line))
        
        print(up_line.get_length())
        print(poly.get_side_lengths())
            # perhatikan hasilnya berbeda dengan panjang awal,
            # awalnya persegi dengan panjang sisi 2.
            # sekarang berbeda karena disesuaikan 
            # dengan perspektif 3 dimensi
        
        self.play(
            poly.animate.shift(UP*2+LEFT),
            up_line.animate.shift(UP*2+LEFT)
        )

        self.play(
            Rotate(poly,30*DEG,axis=OUT, about_point=self.frame.get_center()),
            Rotate(up_line,30*DEG,axis=OUT, about_point=self.frame.get_center()),
        )
        self.embed()
        


class QuadTestFour(GlowDotScene):
    def construct(self):
        plane = NumberPlane(
            x_range=(-16,16,1),
            y_range=(-8,8,1),
        )
        # plane.set_opacity(0.7)
        self.add(plane)
        quad = GlowDot(radius=1, color=PURE_BLUE)
        self.play(FadeIn(quad))
        # self.embed()
        self.play(quad.animate.set_quad_factor(0.5))
        self.play(quad.animate.set_quad_factor(1))
        self.play(quad.animate.set_glow_factor(0.5))
        self.play(quad.animate.set_glow_factor(1))
        self.play(quad.animate.set_glow_factor(0))
        
        self.play(quad.animate.shift(UP*2.5))
        self.play(quad.animate.shift(RIGHT*3))
        
        self.play(self.frame.animate.set_euler_angles(gamma=30*DEG))
        self.play(self.frame.animate.shift(2*UP+LEFT))
        self.play(self.frame.animate.set_height(12))
        
        cam_pos = self.camera_position()
        coords = quad.get_quad_coordinates(cam_pos)

        # Ambil NDC dari semua titik
        ndc_points = [self.get_ndc_for_manim(p[0]) for p in coords]
        sorted_ndc = [
            ndc_points[3],  # kanan atas
            ndc_points[1],  # kiri atas
            ndc_points[0],  # kiri bawah
            ndc_points[2],  # kanan bawah
        ]
        # Konversi ke koordinat Manim
        manim_points = [self.ndc_to_manim(x, y) for x, y, _ in sorted_ndc]

        poly = QuadPolygon(*manim_points, color=YELLOW, stroke_width=2)
        self.play(ShowCreation(poly))
        
        self.wait()
        poly_verts = poly.get_vertices()
        up_line = Line(poly_verts[0],poly_verts[1])
        up_line.set_color(RED)
        
        self.play(ShowCreation(up_line))
        
        print(up_line.get_length())
        print(poly.get_side_lengths())
            # perhatikan hasilnya berbeda dengan panjang awal,
            # awalnya persegi dengan panjang sisi 2.
            # sekarang berbeda karena disesuaikan 
            # dengan perspektif 3 dimensi
        
        self.play(
            poly.animate.shift(UP*2+LEFT),
            up_line.animate.shift(UP*2+LEFT)
        )

        self.play(
            Rotate(poly,30*DEG,axis=OUT, about_point=self.frame.get_center()),
            Rotate(up_line,30*DEG,axis=OUT, about_point=self.frame.get_center()),
        )
        
        self.play(
            poly.animate.scale(12/8, about_point=self.frame.get_center()),
            up_line.animate.scale(12/8, about_point=self.frame.get_center()),
        )
        print(up_line.get_length())
        print(poly.get_side_lengths())
        self.embed()
        