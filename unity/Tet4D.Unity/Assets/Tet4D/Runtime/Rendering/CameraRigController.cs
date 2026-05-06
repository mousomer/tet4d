using UnityEngine;

namespace Tet4D.UnityReplay.Rendering
{
    public sealed class CameraRigController : MonoBehaviour
    {
        [SerializeField] private float orbitSpeed = 3f;
        [SerializeField] private float zoomSpeed = 8f;
        [SerializeField] private float panSpeed = 4f;

        private Vector3 target = new Vector3(1.5f, -1.5f, 0f);
        private float distance = 12f;
        private float yaw = 30f;
        private float pitch = 25f;

        public void FrameBoard(int[] boardShape, int dimension, float sliceStride)
        {
            float width = boardShape.Length > 0 ? boardShape[0] : 4;
            float height = boardShape.Length > 1 ? boardShape[1] : 4;
            float depth = dimension >= 3 && boardShape.Length > 2 ? boardShape[2] : 1;
            float wCount = dimension >= 4 && boardShape.Length > 3 ? boardShape[3] : 1;
            target = new Vector3(
                (width - 1f) * 0.5f + (dimension >= 4 ? (wCount - 1f) * sliceStride * 0.5f : 0f),
                -(height - 1f) * 0.5f,
                depth > 1f ? (depth - 1f) * 0.5f : 0f
            );
            distance = Mathf.Max(10f, width + height + depth + wCount);
            UpdateTransform();
        }

        private void Start()
        {
            if (GetComponent<Camera>() == null)
            {
                gameObject.AddComponent<Camera>();
            }

            UpdateTransform();
        }

        private void Update()
        {
            if (Input.GetMouseButton(1))
            {
                yaw += Input.GetAxis("Mouse X") * orbitSpeed;
                pitch -= Input.GetAxis("Mouse Y") * orbitSpeed;
                pitch = Mathf.Clamp(pitch, -80f, 80f);
            }

            distance = Mathf.Clamp(distance - Input.mouseScrollDelta.y * zoomSpeed, 4f, 60f);
            Vector3 pan = new Vector3(
                Input.GetAxisRaw("Horizontal"),
                0f,
                Input.GetAxisRaw("Vertical")
            );
            if (pan.sqrMagnitude > 0f)
            {
                target += Quaternion.Euler(0f, yaw, 0f) * pan * (panSpeed * Time.deltaTime);
            }

            UpdateTransform();
        }

        private void UpdateTransform()
        {
            Quaternion orbit = Quaternion.Euler(pitch, yaw, 0f);
            transform.position = target + orbit * new Vector3(0f, 0f, -distance);
            transform.LookAt(target);
        }
    }
}
