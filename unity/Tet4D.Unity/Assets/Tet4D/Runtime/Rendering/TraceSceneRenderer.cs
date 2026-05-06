using System.Collections.Generic;
using Tet4D.UnityReplay.TraceReplay;
using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    public sealed class TraceSceneRenderer : MonoBehaviour
    {
        [SerializeField] private float cellScale = 0.9f;
        [SerializeField] private float particleScale = 0.45f;
        [SerializeField] private float eventScale = 0.7f;
        [SerializeField] private float wSlicePadding = 2f;

        private Transform gridRoot;
        private Transform cellRoot;
        private Transform particleRoot;
        private Transform markerRoot;

        public float CurrentSliceStride { get; private set; }

        private void Awake()
        {
            gridRoot = EnsureChild("GridRoot");
            cellRoot = EnsureChild("CellRoot");
            particleRoot = EnsureChild("ParticleRoot");
            markerRoot = EnsureChild("MarkerRoot");
        }

        public void Render(TraceRenderSnapshot snapshot)
        {
            if (snapshot == null)
            {
                return;
            }

            CurrentSliceStride = ComputeSliceStride(snapshot.BoardShape);
            ClearChildren(gridRoot);
            ClearChildren(cellRoot);
            ClearChildren(particleRoot);
            ClearChildren(markerRoot);

            GridReferenceRenderer.Render(
                gridRoot,
                snapshot.BoardShape,
                snapshot.Dimension,
                CurrentSliceStride,
                new Color(0.45f, 0.45f, 0.45f)
            );

            foreach (CellSnapshot cell in snapshot.LockedCells)
            {
                CellGlyphRenderer.Create(
                    cellRoot,
                    ProjectPosition(cell.Position, snapshot.Dimension),
                    Color.gray,
                    cellScale * 0.95f
                );
            }

            foreach (CellSnapshot cell in snapshot.ActiveCells)
            {
                CellGlyphRenderer.Create(
                    cellRoot,
                    ProjectPosition(cell.Position, snapshot.Dimension),
                    ColorForId(cell.ColorId, false),
                    cellScale
                );
            }

            foreach (MarkerSnapshot marker in snapshot.ProbeMarkers)
            {
                EventMarkerRenderer.Create(
                    markerRoot,
                    ProjectPosition(marker.Position, snapshot.Dimension) + Vector3.up * 0.35f,
                    new Color(0.2f, 0.95f, 0.95f),
                    eventScale
                );
            }

            foreach (MarkerSnapshot marker in snapshot.EventMarkers)
            {
                EventMarkerRenderer.Create(
                    markerRoot,
                    ProjectPosition(marker.Position, snapshot.Dimension) + Vector3.up * 0.75f,
                    new Color(1f, 0.85f, 0.25f),
                    eventScale
                );
            }

            foreach (ParticleSnapshot particle in snapshot.Particles)
            {
                float size = Mathf.Max(particleScale, particle.Radius * 1.4f);
                ParticleGlyphRenderer.Create(
                    particleRoot,
                    ProjectPosition(particle.Position, snapshot.Dimension),
                    ColorForId(particle.ColorId, particle.Escaped),
                    size
                );
            }
        }

        private float ComputeSliceStride(int[] boardShape)
        {
            float width = boardShape != null && boardShape.Length > 0 ? boardShape[0] : 4f;
            return width + wSlicePadding;
        }

        private Vector3 ProjectPosition(float[] coordinates, int dimension)
        {
            if (coordinates == null || coordinates.Length == 0)
            {
                return Vector3.zero;
            }

            float x = coordinates.Length > 0 ? coordinates[0] : 0f;
            float y = coordinates.Length > 1 ? -coordinates[1] : 0f;
            float z = coordinates.Length > 2 ? coordinates[2] : 0f;

            if (dimension >= 4 && coordinates.Length > 3)
            {
                x += coordinates[3] * CurrentSliceStride;
            }

            return new Vector3(x, y, z);
        }

        private static Color ColorForId(int colorId, bool escaped)
        {
            Color[] palette =
            {
                new Color(0.85f, 0.85f, 0.85f),
                new Color(0.95f, 0.42f, 0.32f),
                new Color(0.24f, 0.75f, 0.92f),
                new Color(0.44f, 0.82f, 0.36f),
                new Color(0.96f, 0.75f, 0.26f),
                new Color(0.74f, 0.45f, 0.96f),
                new Color(0.96f, 0.54f, 0.22f),
                new Color(0.93f, 0.3f, 0.62f),
                new Color(0.32f, 0.92f, 0.65f)
            };
            Color baseColor = palette[Mathf.Abs(colorId) % palette.Length];
            return escaped ? Color.Lerp(baseColor, Color.white, 0.4f) : baseColor;
        }

        private Transform EnsureChild(string childName)
        {
            Transform child = transform.Find(childName);
            if (child != null)
            {
                return child;
            }

            GameObject childObject = new GameObject(childName);
            childObject.transform.SetParent(transform, false);
            return childObject.transform;
        }

        private static void ClearChildren(Transform parent)
        {
            List<GameObject> toDestroy = new List<GameObject>();
            foreach (Transform child in parent)
            {
                toDestroy.Add(child.gameObject);
            }

            foreach (GameObject child in toDestroy)
            {
                Object.Destroy(child);
            }
        }
    }
}
