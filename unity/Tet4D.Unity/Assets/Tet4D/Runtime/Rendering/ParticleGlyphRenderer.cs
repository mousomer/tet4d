using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    internal static class ParticleGlyphRenderer
    {
        public static GameObject Create(Transform parent, Vector3 position, Color color, float scale)
        {
            GameObject glyph = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            glyph.name = "ParticleGlyph";
            glyph.transform.SetParent(parent, false);
            glyph.transform.position = position;
            glyph.transform.localScale = Vector3.one * scale;
            Object.Destroy(glyph.GetComponent<Collider>());
            Renderer renderer = glyph.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = new Material(Shader.Find("Standard"));
                renderer.material.color = color;
            }

            return glyph;
        }
    }
}
