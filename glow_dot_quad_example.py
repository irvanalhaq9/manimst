from manimlib import *

class QuadTest(InteractiveScene):
    def construct(self):
        quad = GlowDot(radius=1, color=PURE_BLUE)
        self.play(FadeIn(quad))
        # self.embed()
        self.play(quad.animate.set_quad_factor(0.5))
        self.play(quad.animate.set_quad_factor(1))
        self.play(quad.animate.set_glow_factor(0.5))
        self.play(quad.animate.set_glow_factor(1))
        self.play(quad.animate.set_glow_factor(0))
        
        sq = Square()
        sq.set_stroke(width=1, color=YELLOW)
        self.play(ShowCreation(sq))
        
        self.play(quad.animate.shift(UP*2.5))
        self.play(sq.animate.shift(UP*2.5))
        
        self.play(self.frame.animate.set_euler_angles(gamma=30*DEG))

        
        # self.embed()
        self.play(self.frame.animate.increment_theta(10*DEG))
        #
        self.play(self.frame.animate.set_height(15))
        self.play(self.frame.animate.shift(DL*3))
        self.play(self.frame.animate.shift(LEFT*5))
        
        # fix in frame
        self.play(sq.animate.fix_in_frame())
        self.play(sq.animate.unfix_from_frame())
        self.play(sq.animate.set_fixed_in_frame_factor(0.5))
        print(sq.get_fixed_in_frame_factor())
        
        # anti alias width
        self.play(quad.animate.fix_in_frame())
        self.play(quad.animate.set_anti_alias_width(10))
        self.play(quad.animate.set_anti_alias_width(100))
        self.play(quad.animate.set_anti_alias_width(1))
        self.play(quad.animate.set_anti_alias_width(0))
        self.play(quad.animate.set_anti_alias_width(2))
        self.embed()
        
