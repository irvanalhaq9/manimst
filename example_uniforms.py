# pada kode ini, akan dieksplorasi kegunaan dari uniforms
from manimlib import *

class RectangleUniforms(InteractiveScene):
    def construct(self):
        rec = Rectangle()
        rec.set_stroke(color=RED, width=16)
        rec.set_fill(color=BLUE,opacity=1)
        self.add(rec)
        self.embed()
        rec.get_uniforms()
        # {'is_fixed_in_frame': 0.0,
        # 'shading': array([0., 0., 0.]),
        # 'clip_plane': array([0., 0., 0., 0.]),
        # 'anti_alias_width': 1.5,
        # 'joint_type': 1,
        # 'flat_stroke': 0.0,
        # 'scale_stroke_with_zoom': 0.0}
        #
        # 1. scale_stroke_with_zoom: silakan zoom perkecil, akan terlihat bahwa
        #    stroke-nya tetap, hingga menutupi fill-nya, ganti agar sesuai.
        self.play(self.frame.animate.set_height(70))
        rec.set_scale_stroke_with_zoom(True)
        self.play(self.frame.animate.to_default_state())
        
        # 2. joint_type: no_joint, auto, bevel, miter. 
        #    Auto adalah kombinasi dari bevel dan miter
        rec.set_joint_type("no_joint")
        rec.set_joint_type("bevel")
        rec.set_joint_type("miter")
        rec.set_joint_type("auto")
        
        # 3. flat_stroke: ketebalan pada sumbu z
        rec.rotate(-PI/2, axis=RIGHT) # hanya terlihat sisinya dari bawah
        rec.set_flat_stroke(True) # sekarang tidak ada ketebalan sumbu z
        self.play(Rotate(rec,PI/4, axis=RIGHT))
        #  
        
        # 4. shading: pencahayaan, setelah mengatur ini, harus diputar-putar 
        #    perspective-nya, agar kelihatan bedanya. 
        #    Dengan posisi sekarang sudah bisa terlihat
        rec.set_shading(reflectiveness=0, gloss=1, shadow=0)
        #  terlihat di bagian kiri bawah warnanya hampir putih
        
        # 5. clip_plane: memotong objeck yang kelihatan di layar 
        #    bisa horizontal, vertikal, atau diagonal
        rec.set_clip_plane([1, -2, 0], threshold=1)
        #  terlihat terpotong diagonal di sebagian kiri atas
        
        # 6. anti_alias_width: mengatur stroke halus atau bergerigi 
        #    kalau 0, bergerigi
        #    kalau 1.5 sampai 3, umum digunakan
        #    kalau di atas 10, terlihat blur
        rec.set_anti_alias_width(0)
        self.frame.set_height(4)
        self.frame.increment_theta(PI/8)
        self.frame.increment_phi(PI/8) # ternyata ini ada batasannya, sedangkan yang lain tidak
        self.frame.increment_gamma(PI/8)
        rec.rotate(45*DEG) # sekaran terlihat sisinya bergerigi
        self.play(rec.animate.set_anti_alias_width(11),run_time=2,rate_func=linear)
        self.play(rec.animate.set_anti_alias_width(0),run_time=2,rate_func=linear)
        self.play(self.frame.animate.to_default_state())
        #  sekarang terlihat hampir semua rec berwarna putih, 
        #  efek dari shading
        
        # 7. is_fixed_in_frame: rec tidak berubah meskipun frame berubah 
        rec.fix_in_frame()
        rec.rotate(-45*DEG)
        self.frame.increment_theta(PI/8)
        self.frame.set_height(4)
        self.frame.increment_phi(-PI/8) # tapi shading bisa terpengaruh
        self.frame.increment_gamma(PI/8)
        self.frame.set_height(40)
        rec.unfix_from_frame()
        self.play(self.frame.animate.move_to([10,5,10]))
        self.play(Rotate(self.frame,PI/20,about_point=RIGHT,run_time=4))
        self.play(self.frame.animate.to_default_state())
        
        # back to default
        rec.get_uniforms()
        self.play(rec.animate.set_shading(0,0,0),run_time=2)
        rec.deactivate_clip_plane()
        rec.set_joint_type("auto")
        rec.rotate(PI/4,axis=RIGHT)
        rec.set_flat_stroke(False)
        rec.set_anti_alias_width(2)
        
        # depth test
        rec.apply_depth_test()
        rec.deactivate_depth_test()
        
        
        