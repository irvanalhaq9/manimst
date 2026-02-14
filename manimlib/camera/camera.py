from __future__ import annotations

import moderngl
from moderngl_window.timers.clock import Timer
import numpy as np
import OpenGL.GL as gl
from PIL import Image

from manimlib.camera.camera_frame import CameraFrame
from manimlib.constants import BLACK
from manimlib.constants import DEFAULT_RESOLUTION
from manimlib.constants import FRAME_HEIGHT
from manimlib.constants import FRAME_WIDTH
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.mobject import Point
from manimlib.utils.color import color_to_rgba

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional
    from manimlib.typing import ManimColor, Vect3
    from manimlib.window import Window


class Camera(object):
    def __init__(
        self,
        window: Optional[Window] = None,
        background_image: Optional[str] = None,
        frame_config: dict = dict(),
        # Note: frame height and width will be resized to match this resolution aspect ratio
        resolution=DEFAULT_RESOLUTION,
        fps: int = 30,
        background_color: ManimColor = BLACK,
        background_opacity: float = 1.0,
        # Points in vectorized mobjects with norm greater
        # than this value will be rescaled.
        max_allowable_norm: float = FRAME_WIDTH,
        image_mode: str = "RGBA",
        n_channels: int = 4,
        pixel_array_dtype: type = np.uint8,
        light_source_position: Vect3 = np.array([-10, 10, 10]),
        # Although vector graphics handle antialiasing fine
        # without multisampling, for 3d scenes one might want
        # to set samples to be greater than 0.
        samples: int = 0,
    ):
        self.window = window
        self.background_image = background_image
        self.default_pixel_shape = resolution  # Rename?
        self.fps = fps
        self.max_allowable_norm = max_allowable_norm
        self.image_mode = image_mode
        self.n_channels = n_channels
        self.pixel_array_dtype = pixel_array_dtype
        self.light_source_position = light_source_position
        self.samples = samples

        self.rgb_max_val: float = np.iinfo(self.pixel_array_dtype).max
        self.background_rgba: list[float] = list(color_to_rgba(
            background_color, background_opacity
        ))
        self.uniforms = dict()
        self.init_frame(**frame_config)
        self.init_context()
        self.init_fbo()
        self.init_light_source()
        self.timer = Timer()
        self.timer.start()

    def init_frame(self, **config) -> None:
        self.frame = CameraFrame(**config)

    def init_context(self) -> None:
        if self.window is None:
            self.ctx: moderngl.Context = moderngl.create_standalone_context()
        else:
            self.ctx: moderngl.Context = self.window.ctx

        self.ctx.enable(moderngl.PROGRAM_POINT_SIZE)
        self.ctx.enable(moderngl.BLEND)

    def init_fbo(self) -> None:
        # This is the buffer used when writing to a video/image file
        self.fbo_for_files = self.get_fbo(self.samples)

        # This is the frame buffer we'll draw into when emitting frames
        self.draw_fbo = self.get_fbo(samples=0)

        if self.window is None:
            self.window_fbo = None
            self.fbo = self.fbo_for_files
        else:
            self.window_fbo = self.ctx.detect_framebuffer()
            self.fbo = self.window_fbo

        self.fbo.use()

    def init_light_source(self) -> None:
        self.light_source = Point(self.light_source_position)

    def use_window_fbo(self, use: bool = True):
        assert self.window is not None
        if use:
            self.fbo = self.window_fbo
        else:
            self.fbo = self.fbo_for_files

    # Methods associated with the frame buffer
    def get_fbo(
        self,
        samples: int = 0
    ) -> moderngl.Framebuffer:
        return self.ctx.framebuffer(
            color_attachments=self.ctx.texture(
                self.default_pixel_shape,
                components=self.n_channels,
                samples=samples,
            ),
            depth_attachment=self.ctx.depth_renderbuffer(
                self.default_pixel_shape,
                samples=samples
            )
        )

    def clear(self) -> None:
        self.fbo.clear(*self.background_rgba)
        if self.window:
            self.window.clear(*self.background_rgba)

    def blit(self, src_fbo, dst_fbo):
        """
        Copy blocks between fbo's using Blit
        """
        gl.glBindFramebuffer(gl.GL_READ_FRAMEBUFFER, src_fbo.glo)
        gl.glBindFramebuffer(gl.GL_DRAW_FRAMEBUFFER, dst_fbo.glo)
        gl.glBlitFramebuffer(
            *src_fbo.viewport,
            *dst_fbo.viewport,
            gl.GL_COLOR_BUFFER_BIT, gl.GL_LINEAR
        )

    def get_raw_fbo_data(self, dtype: str = 'f1') -> bytes:
        self.blit(self.fbo, self.draw_fbo)
        return self.draw_fbo.read(
            viewport=self.draw_fbo.viewport,
            components=self.n_channels,
            dtype=dtype,
        )

    def get_image(self) -> Image.Image:
        return Image.frombytes(
            'RGBA',
            self.get_pixel_shape(),
            self.get_raw_fbo_data(),
            'raw', 'RGBA', 0, -1
        )

    def get_pixel_array(self) -> np.ndarray:
        raw = self.get_raw_fbo_data(dtype='f4')
        flat_arr = np.frombuffer(raw, dtype='f4')
        arr = flat_arr.reshape([*reversed(self.draw_fbo.size), self.n_channels])
        arr = arr[::-1]
        # Convert from float
        return (self.rgb_max_val * arr).astype(self.pixel_array_dtype)

    # Needed?
    def get_texture(self) -> moderngl.Texture:
        texture = self.ctx.texture(
            size=self.fbo.size,
            components=4,
            data=self.get_raw_fbo_data(),
            dtype='f4'
        )
        return texture

    # Getting camera attributes
    def get_pixel_size(self) -> float:
        return self.frame.get_width() / self.get_pixel_shape()[0]

    def get_pixel_shape(self) -> tuple[int, int]:
        return self.fbo.size

    def get_pixel_width(self) -> int:
        return self.get_pixel_shape()[0]

    def get_pixel_height(self) -> int:
        return self.get_pixel_shape()[1]

    def get_aspect_ratio(self):
        pw, ph = self.get_pixel_shape()
        return pw / ph

    def get_frame_height(self) -> float:
        return self.frame.get_height()

    def get_frame_width(self) -> float:
        return self.frame.get_width()

    def get_frame_shape(self) -> tuple[float, float]:
        return (self.get_frame_width(), self.get_frame_height())

    def get_frame_center(self) -> np.ndarray:
        return self.frame.get_center()

    def get_location(self) -> tuple[float, float, float]:
        return self.frame.get_implied_camera_location()

    def resize_frame_shape(self, fixed_dimension: bool = False) -> None:
        """
        Changes frame_shape to match the aspect ratio
        of the pixels, where fixed_dimension determines
        whether frame_height or frame_width
        remains fixed while the other changes accordingly.
        """
        frame_height = self.get_frame_height()
        frame_width = self.get_frame_width()
        aspect_ratio = self.get_aspect_ratio()
        if not fixed_dimension:
            frame_height = frame_width / aspect_ratio
        else:
            frame_width = aspect_ratio * frame_height
        self.frame.set_height(frame_height, stretch=True)
        self.frame.set_width(frame_width, stretch=True)

    # Rendering
    def capture(self, *mobjects: Mobject) -> None:
        self.clear()
        self.refresh_uniforms()
        self.fbo.use()
        for mobject in mobjects:
            mobject.render(self.ctx, self.uniforms)

        if self.window:
            self.window.swap_buffers()
            if self.fbo is not self.window_fbo:
                self.blit(self.fbo, self.window_fbo)
                self.window.swap_buffers()

    def refresh_uniforms(self) -> None:
        frame = self.frame
        view_matrix = frame.get_view_matrix()
        light_pos = self.light_source.get_location()
        cam_pos = self.frame.get_implied_camera_location()
        now = self.timer.time

        self.uniforms.update(
            view=tuple(view_matrix.T.flatten()),
            frame_scale=frame.get_scale(),
            frame_rescale_factors=(
                2.0 / FRAME_WIDTH,
                2.0 / FRAME_HEIGHT,
                frame.get_scale() / frame.get_focal_distance(),
            ),
            pixel_size=self.get_pixel_size(),
            camera_position=tuple(cam_pos),
            light_position=tuple(light_pos),
            time=now*2,
        )

    def info_uniforms(self) -> None:
        frame = self.frame
        uniforms = self.uniforms
        view_matrix = frame.get_view_matrix()
        frf = uniforms["frame_rescale_factors"]
        print("view_matrix:\n",view_matrix)
        print("light_position:",uniforms["light_position"])
        print("camera_position:",uniforms["camera_position"])
        print("FRAME_WIDTH:",FRAME_WIDTH)
        print("FRAME_HEIGHT:",FRAME_HEIGHT)
        print("frame_scale:",uniforms["frame_scale"])
        print("focal_distance:",frame.get_focal_distance())
        print("pixel_size:",uniforms["pixel_size"])
        print("frame_rescale_factors:\n",frf)

    def emit_gl_Position(
        self,
        point: np.ndarray,
        is_fixed_in_frame: float = 0.0,
        ) -> np.ndarray:
        """
        Fungsi ini sesuai dengan shader, yaitu mentransformasi koordinat manim
        menjadi koordinat opengl dengan menerapkan projection dari
        view_matrix. gl_Position ini akan digunakan untuk membuat 
        koordinat Normalized Device Coordinate (NDC).
        """
        frame = self.frame
        uniforms = self.uniforms
        view = frame.get_view_matrix()
        frf = uniforms["frame_rescale_factors"]
        
        # 1. buat vektor 4D dari point
        result = np.append(point,1.0)
        
        # 2. Transformasi view, lalu mix
        transformed = view @ result
        result = (1.0-is_fixed_in_frame)*transformed+is_fixed_in_frame*result
        
        # 3. rescale
        result[:3] *= frf
        
        # 4. set w dan manipulasi z
        result[3] = 1 - result[2]
        result[2] *= -0.1
        
        # 5. hasil akhir
        gl_Position = result
        
        return gl_Position
    
    def get_ndc_coordinate(self,point: np.ndarray,**kwargs) -> np.ndarray:
        """
        Ini adalah koordinat di layar yang sebenarnya. 
        Koordinat setelah penyesuaian perspektif 3 dimensi.
        Ini menghasilkan NDC: Yaitu koordinat x,y,z dibagi w
        Nilai itu semua dari gl_Position. x dan y adalah koodinat di layar
        atau window. z itu digunakan untuk depth test, jadi tidak mempengaruhi
        koordinat di layar. Setelah dibagi w itulah yang menghasilkan perspektif
        3 dimensi.
        """
        gl_Position = self.emit_gl_Position(point,**kwargs)
        coord = gl_Position[:3]/gl_Position[3]
        return coord

# Mostly just defined so old scenes don't break
class ThreeDCamera(Camera):
    def __init__(self, samples: int = 4, **kwargs):
        super().__init__(samples=samples, **kwargs)
