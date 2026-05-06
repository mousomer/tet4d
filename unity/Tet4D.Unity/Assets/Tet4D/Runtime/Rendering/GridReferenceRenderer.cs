using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    internal static class GridReferenceRenderer
    {
        public static void Render(
            Transform parent,
            int[] boardShape,
            int dimension,
            float sliceStride,
            Color color
        )
        {
            int width = boardShape.Length > 0 ? Mathf.Max(boardShape[0], 1) : 4;
            int height = boardShape.Length > 1 ? Mathf.Max(boardShape[1], 1) : 4;
            int depth = dimension >= 3 && boardShape.Length > 2 ? Mathf.Max(boardShape[2], 1) : 1;
            int sliceCount = dimension >= 4 && boardShape.Length > 3 ? Mathf.Max(boardShape[3], 1) : 1;

            for (int sliceIndex = 0; sliceIndex < sliceCount; sliceIndex += 1)
            {
                Vector3 sliceOffset = dimension >= 4
                    ? new Vector3(sliceStride * sliceIndex, 0f, 0f)
                    : Vector3.zero;
                CreateBox(parent, width, height, depth, sliceOffset, color);
            }
        }

        private static void CreateBox(
            Transform parent,
            int width,
            int height,
            int depth,
            Vector3 offset,
            Color color
        )
        {
            float xMin = -0.5f + offset.x;
            float xMax = width - 0.5f + offset.x;
            float yMin = 0.5f + offset.y;
            float yMax = -height + 0.5f + offset.y;
            float zMin = depth <= 1 ? 0f + offset.z : -0.5f + offset.z;
            float zMax = depth <= 1 ? 0f + offset.z : depth - 0.5f + offset.z;

            CreateEdge(parent, new Vector3(xMin, yMin, zMin), new Vector3(xMax, yMin, zMin), color);
            CreateEdge(parent, new Vector3(xMin, yMax, zMin), new Vector3(xMax, yMax, zMin), color);
            CreateEdge(parent, new Vector3(xMin, yMin, zMax), new Vector3(xMax, yMin, zMax), color);
            CreateEdge(parent, new Vector3(xMin, yMax, zMax), new Vector3(xMax, yMax, zMax), color);
            CreateEdge(parent, new Vector3(xMin, yMin, zMin), new Vector3(xMin, yMax, zMin), color);
            CreateEdge(parent, new Vector3(xMax, yMin, zMin), new Vector3(xMax, yMax, zMin), color);
            CreateEdge(parent, new Vector3(xMin, yMin, zMax), new Vector3(xMin, yMax, zMax), color);
            CreateEdge(parent, new Vector3(xMax, yMin, zMax), new Vector3(xMax, yMax, zMax), color);

            if (depth > 1)
            {
                CreateEdge(parent, new Vector3(xMin, yMin, zMin), new Vector3(xMin, yMin, zMax), color);
                CreateEdge(parent, new Vector3(xMax, yMin, zMin), new Vector3(xMax, yMin, zMax), color);
                CreateEdge(parent, new Vector3(xMin, yMax, zMin), new Vector3(xMin, yMax, zMax), color);
                CreateEdge(parent, new Vector3(xMax, yMax, zMin), new Vector3(xMax, yMax, zMax), color);
            }
        }

        private static void CreateEdge(Transform parent, Vector3 start, Vector3 end, Color color)
        {
            GameObject edge = GameObject.CreatePrimitive(PrimitiveType.Cube);
            edge.name = "GridEdge";
            edge.transform.SetParent(parent, false);
            edge.transform.position = (start + end) * 0.5f;
            edge.transform.rotation = Quaternion.FromToRotation(Vector3.right, end - start);
            edge.transform.localScale = new Vector3((end - start).magnitude, 0.03f, 0.03f);
            Object.Destroy(edge.GetComponent<Collider>());

            Renderer renderer = edge.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material = new Material(Shader.Find("Standard"));
                renderer.material.color = color;
            }
        }
    }
}
