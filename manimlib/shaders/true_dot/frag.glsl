#version 330

uniform float glow_factor;
uniform mat4 perspective;
uniform float quad_factor; // 0 for circle, 1 for square
uniform float time;
uniform float use_dynamic_color;
uniform float blink_factor;
uniform float blink_type;   // 0: Brightness, 1: Hue, 2: Saturation, 3: Value

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

// Fungsi konversi RGB ke HSV
vec3 rgb_to_hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

// Fungsi konversi HSV ke RGB
vec3 hsv_to_rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

void main() {
    // Compute distances for circle and square
    float r_circle = length(uv_coords.xy);
    float r_square = max(abs(uv_coords.x), abs(uv_coords.y));
    // Interpolate between circle and square
    float r = mix(r_circle, r_square, quad_factor);
    // Discard pixels outside shape
    if (r > 1.0) discard;

    // Warna dinamis default (dari use_dynamic_color)
    vec4 dynamic_color = vec4(
        sin(time + 0.0) * 0.5 + 0.5,
        sin(time + 2.1) * 0.5 + 0.5,
        sin(time + 4.2) * 0.5 + 0.5,
        color.a
    );
    // frag_color = mix(color, dynamic_color, use_dynamic_color);

    // Hitung efek berkelap-kelip berdasarkan blink_type
    vec4 blinking_color = color;
    float t = time * 0.5 + center.x + center.y + center.z;
    if (blink_type < 0.5) { // Brightness
        float brightness = 0.5 + 0.5 * sin(t);
        blinking_color = vec4(color.rgb * brightness, color.a);
    } else if (blink_type < 1.5) { // Hue
        vec3 hsv = rgb_to_hsv(color.rgb);
        hsv.x = mod(hsv.x + 0.1 * sin(t), 1.0);
        blinking_color = vec4(hsv_to_rgb(hsv), color.a);
    } else if (blink_type < 2.5) { // Saturation
        vec3 hsv = rgb_to_hsv(color.rgb);
        hsv.y = 0.5 + 0.5 * sin(t);
        blinking_color = vec4(hsv_to_rgb(hsv), color.a);
    } else { // Value
        vec3 hsv = rgb_to_hsv(color.rgb);
        hsv.z = 0.5 + 0.5 * sin(t);
        blinking_color = vec4(hsv_to_rgb(hsv), color.a);
    }
    // Pilih antara warna asli, dynamic_color, dan blinking_color
    vec4 final_color = color;
    if (use_dynamic_color > 0.0) {
        final_color = mix(color, dynamic_color, use_dynamic_color);
    }
    final_color = mix(final_color, blinking_color, blink_factor);

    frag_color = final_color;

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