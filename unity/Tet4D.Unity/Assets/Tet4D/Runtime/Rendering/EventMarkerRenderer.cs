using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    internal static class EventMarkerRenderer
    {
        public static GameObject Create(Transform parent, Vector3 position, Color color, float scale)
        {
            GameObject glyph = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            glyph.name = "EventMarker";
            glyph.transform.SetParent(parent, false);
            glyph.transform.position = position;
            glyph.transform.localScale = new Vector3(scale * 0.3f, scale * 0.5f, scale * 0.3f);
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
