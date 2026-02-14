from __future__ import annotations

import moderngl
import numpy as np

from manimlib.constants import GREY_C, YELLOW
from manimlib.constants import ORIGIN, NULL_POINTS
from manimlib.mobject.mobject import Mobject
from manimlib.mobject.types.point_cloud_mobject import PMobject
from manimlib.utils.iterables import resize_with_interpolation

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy.typing as npt
    from typing import Sequence, Tuple
    from manimlib.typing import ManimColor, Vect3, Vect3Array, Self


DEFAULT_DOT_RADIUS = 0.05
DEFAULT_GLOW_DOT_RADIUS = 0.2
DEFAULT_GRID_HEIGHT = 6
DEFAULT_BUFF_RATIO = 0.5


class DotCloud(PMobject):
    shader_folder: str = "true_dot"
    render_primitive: int = moderngl.POINTS
    data_dtype: Sequence[Tuple[str, type, Tuple[int]]] = [
        ('point', np.float32, (3,)),
        ('radius', np.float32, (1,)),
        ('rgba', np.float32, (4,)),
    ]

    blink_type_map = {
        "brightness": 0.0,
        "hue": 1.0,
        "saturation": 2.0,
        "value": 3.0
    }

    def __init__(
        self,
        points: Vect3Array = NULL_POINTS,
        color: ManimColor = GREY_C,
        opacity: float = 1.0,
        radius: float = DEFAULT_DOT_RADIUS,
        glow_factor: float = 0.0,
        anti_alias_width: float = 2.0,
        quad_factor: float = 0.0,  # circle to square factor
        use_dynamic_color: float = 0.0,
        blink_factor: float = 0.0,
        blink_type: str = "brightness",
        **kwargs
    ):
        self.radius = radius
        self.glow_factor = glow_factor
        self.anti_alias_width = anti_alias_width
        self.quad_factor = quad_factor
        self.use_dynamic_color = use_dynamic_color
        self.blink_factor = blink_factor
        self.blink_type = blink_type

        super().__init__(
            color=color,
            opacity=opacity,
            **kwargs
        )
        self.set_radius(self.radius)

        if points is not None:
            self.set_points(points)

    def init_uniforms(self) -> None:
        super().init_uniforms()
        self.uniforms["glow_factor"] = self.glow_factor
        self.uniforms["anti_alias_width"] = self.anti_alias_width
        self.uniforms["quad_factor"] = self.quad_factor
        self.uniforms["use_dynamic_color"] = self.use_dynamic_color
        self.uniforms["blink_factor"] = self.blink_factor
        self.uniforms["blink_type"] = self.blink_type_map[self.blink_type]

    def to_grid(
        self,
        n_rows: int,
        n_cols: int,
        n_layers: int = 1,
        buff_ratio: float | None = None,
        h_buff_ratio: float = 1.0,
        v_buff_ratio: float = 1.0,
        d_buff_ratio: float = 1.0,
        height: float = DEFAULT_GRID_HEIGHT,
    ) -> Self:
        n_points = n_rows * n_cols * n_layers
        points = np.repeat(range(n_points), 3, axis=0).reshape((n_points, 3))
        points[:, 0] = points[:, 0] % n_cols
        points[:, 1] = (points[:, 1] // n_cols) % n_rows
        points[:, 2] = points[:, 2] // (n_rows * n_cols)
        self.set_points(points.astype(float))

        if buff_ratio is not None:
            v_buff_ratio = buff_ratio
            h_buff_ratio = buff_ratio
            d_buff_ratio = buff_ratio

        radius = self.get_radius()
        ns = [n_cols, n_rows, n_layers]
        brs = [h_buff_ratio, v_buff_ratio, d_buff_ratio]
        self.set_radius(0)
        for n, br, dim in zip(ns, brs, range(3)):
            self.rescale_to_fit(2 * radius * (1 + br) * (n - 1), dim, stretch=True)
        self.set_radius(radius)
        if height is not None:
            self.set_height(height)
        self.center()
        return self

    @Mobject.affects_data
    def set_radii(self, radii: npt.ArrayLike) -> Self:
        n_points = self.get_num_points()
        radii = np.array(radii).reshape((len(radii), 1))
        self.data["radius"][:] = resize_with_interpolation(radii, n_points)
        self.refresh_bounding_box()
        return self

    def get_radii(self) -> np.ndarray:
        return self.data["radius"]

    @Mobject.affects_data
    def set_radius(self, radius: float) -> Self:
        data = self.data if self.get_num_points() > 0 else self._data_defaults
        data["radius"][:] = radius
        self.refresh_bounding_box()
        return self

    def get_radius(self) -> float:
        return self.get_radii().max()

    def scale_radii(self, scale_factor: float) -> Self:
        self.set_radius(scale_factor * self.get_radii())
        return self

    def set_glow_factor(self, glow_factor: float) -> Self:
        self.uniforms["glow_factor"] = glow_factor
        return self

    def get_glow_factor(self) -> float:
        return self.uniforms["glow_factor"]

    def set_anti_alias_width(self, anti_alias_width: float = 2.0) -> Self:
        self.uniforms["anti_alias_width"] = anti_alias_width
        return self

    def get_anti_alias_width(self) -> float:
        return self.uniforms["anti_alias_width"]

    def set_quad_factor(self, quad_factor: float = 0.0) -> Self:
        """Set shape factor between circle and square."""
        quad_factor = max(0.0, min(1.0, quad_factor))  # Simplified clamping
        self.uniforms["quad_factor"] = quad_factor
        return self
    
    def get_quad_factor(self) -> float:
        return self.uniforms["quad_factor"]

    def set_dynamic_color(self, dynamic_color: float = 1.0) -> Self:
        dynamic_color = max(0.0, min(1.0, dynamic_color))  # Simplified clamping
        self.uniforms["use_dynamic_color"] = dynamic_color
        return self

    def get_dynamic_color(self) -> float:
        return self.uniforms["use_dynamic_color"]

    def set_blink_factor(self, blink_factor: float = 1.0) -> Self:
        blink_factor = max(0.0, min(1.0, blink_factor))  # Simplified clamping
        self.uniforms["blink_factor"] = blink_factor
        return self

    def get_blink_factor(self) -> float:
        return self.uniforms["blink_factor"]

    def set_blink_type(self, blink_type: str = "brightness") -> Self:
        self.uniforms["blink_type"] = self.blink_type_map[blink_type]
        return self

    def get_blink_type(self) -> float:
        return self.uniforms["blink_type"]

    def compute_bounding_box(self) -> Vect3Array:
        bb = super().compute_bounding_box()
        radius = self.get_radius()
        bb[0] += np.full((3,), -radius)
        bb[2] += np.full((3,), radius)
        return bb

    def scale(
        self,
        scale_factor: float | npt.ArrayLike,
        scale_radii: bool = True,
        **kwargs
    ) -> Self:
        super().scale(scale_factor, **kwargs)
        if scale_radii:
            self.set_radii(scale_factor * self.get_radii())
        return self

    def make_3d(
        self,
        reflectiveness: float = 0.5,
        gloss: float = 0.1,
        shadow: float = 0.2
    ) -> Self:
        self.set_shading(reflectiveness, gloss, shadow)
        self.apply_depth_test()
        return self


class TrueDot(DotCloud):
    def __init__(self, center: Vect3 = ORIGIN, **kwargs):
        super().__init__(points=np.array([center]), **kwargs)


class GlowDots(DotCloud):
    def __init__(
        self,
        points: Vect3Array = NULL_POINTS,
        color: ManimColor = YELLOW,
        radius: float = DEFAULT_GLOW_DOT_RADIUS,
        glow_factor: float = 2.0,
        quad_factor: float = 0.0,  # Default to circle
        **kwargs,
    ):
        super().__init__(
            points,
            color=color,
            radius=radius,
            glow_factor=glow_factor,
            quad_factor=quad_factor,
            **kwargs,
        )


class GlowDot(GlowDots):
    def __init__(self, center: Vect3 = ORIGIN, **kwargs):
        super().__init__(points=np.array([center]), **kwargs)

    def get_quad_coordinates(
        self,
        camera_position: np.ndarray,
    ) -> np.ndarray:
        """
        Ini menghasilkan quad atau segi-4 untuk dot, seperti yang ada di
        geometry_shader dari true_dot.
        
        """
        point = self.data["point"]
        radius = self.data["radius"]
            # menghasilkan vektor yang menghadap kamera
        to_cam_vector = camera_position - point
        to_cam_normal = to_cam_vector / np.linalg.norm(to_cam_vector)
            # vektor kanan tegak lurus terhadap vektor kamera
        right_vector = np.cross(np.array([0.0,1.0,1.0]), to_cam_normal)
        right_normal = right_vector/np.linalg.norm(right_vector)
        right = radius * right_normal
            # vektor atas tegak lurus terhadap 2 vektor lainnya.
            # di ruang 3 dimensi hanya ada 3 vektor yang saling tegak lurus
            # satu-sama lain, tidak bisa lebih.
            # jadi ini akan menghasilkan bidang yang selalu menghadap kamera.
        up_vector = np.cross(to_cam_normal, right)
        up_normal = up_vector/np.linalg.norm(up_vector)
        up = radius * up_normal
        
        # offset: sudut-sudut dari quad
        offsets = [(-1,-1),(-1,1),(1,-1),(1,1)]
        corners = [point+i*right+j*up for i,j in offsets]
        return np.array(corners)
