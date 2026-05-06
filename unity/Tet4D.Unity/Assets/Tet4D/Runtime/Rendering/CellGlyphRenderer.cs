using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    internal static class CellGlyphRenderer
    {
        public static GameObject Create(Transform parent, Vector3 position, Color color, float scale)
        {
            GameObject glyph = GameObject.CreatePrimitive(PrimitiveType.Cube);
            glyph.name = "CellGlyph";
            glyph.transform.SetParent(parent, false);
            glyph.transform.position = position;
            glyph.transform.localScale = Vector3.one * scale;
            Object.Destroy(glyph.GetComponent<Collider>());
            ApplyColor(glyph, color);
            return glyph;
        }

        private static void ApplyColor(GameObject glyph, Color color)
        {
            Renderer renderer = glyph.GetComponent<Renderer>();
            if (renderer == null)
            {
                return;
            }

            renderer.material = new Material(Shader.Find("Standard"));
            renderer.material.color = color;
        }
    }
}
