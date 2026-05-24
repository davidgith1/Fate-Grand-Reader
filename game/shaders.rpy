
init -1 python:
    renpy.register_shader("example.lighting", variables="""
        uniform mat4 u_model__inverse_transpose;
        uniform sampler2D u_tex_diffuse;
        varying vec3 v_normal;
        varying vec2 v_tex_coord;
        attribute vec3 a_normal;
        attribute vec2 a_tex_coord;
    """, vertex_201="""
        v_normal = (u_model__inverse_transpose * vec4(a_normal, 1.0)).xyz;
        v_tex_coord = a_tex_coord;
    """, fragment_201="""
        // Sunlight vector coming from the front-right side
        vec3 lightDir = normalize(vec3(0.5, 0.2, 1.0));
        vec3 normal = normalize(v_normal);
        
        // Calculate diffuse light intensity
        float lambertian = max(dot(normal, lightDir), 0.0);
        
        // Get base texture pixel color
        vec4 diffuse_color = texture2D(u_tex_diffuse, v_tex_coord.xy);
        
        // Hardcoded diffuse/specular colors to completely avoid KeyError crashes!
        vec3 fallback_diffuse = vec3(1.0, 1.0, 1.0);
        vec3 fallback_specular = vec3(0.4, 0.4, 0.4); // Subtle white shine for atmosphere
        
        // Apply light reflection + subtle ambient light (0.15) so the dark side isn't pitch black
        vec3 light_reflection = (lambertian + 0.15) * fallback_diffuse; 
        diffuse_color.rgb *= light_reflection;

        // Calculate specular highlights (ocean reflection glints)
        vec3 viewDir = normalize(vec3(0.0, 0.0, -1.0));
        vec3 halfDir = normalize(lightDir + viewDir);
        float specular = pow(max(dot(normal, halfDir), 0.0), 16.0);
        vec4 specular_color = vec4(fallback_specular * specular, 0.0);
        
        gl_FragColor = diffuse_color + specular_color;
        
        // Smoothly discard transparent edges without jagged aliasing
        if (gl_FragColor.a < 0.05) {
            discard;
        }
    """)