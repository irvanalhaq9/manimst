#version 330

uniform float glow_factor;
uniform mat4 perspective;
uniform float quad_factor; // 0 for circle, 1 for square

in vec4 color;
in float scaled_aaw;
in vec3 point;
in vec3 to_cam;
in vec3 center;
in float radius;
in vec2 uv_coords;

out vec4 frag_color;

// This includes a declaration of uniform vec3 shading
#INSERT finalize_color.glsl

void main() {
    // Compute distances for circle and square
    float r_circle = length(uv_coords.xy);
    float r_square = max(abs(uv_coords.x), abs(uv_coords.y));
    // Interpolate between circle and square
    float r = mix(r_circle, r_square, quad_factor);
    // Discard pixels outside shape
    if (r > 1.0) discard;

    frag_color = color;

    if(glow_factor > 0){
        frag_color.a *= pow(1 - r, glow_factor);
    }

    if(shading != vec3(0.0)){
        vec3 point_3d = point + radius * sqrt(1 - r * r) * to_cam;
        vec3 normal = normalize(point_3d - center);
        frag_color = finalize_color(frag_color, point_3d, normal);
    }

    frag_color.a *= smoothstep(1.0, 1.0 - scaled_aaw, r);
}