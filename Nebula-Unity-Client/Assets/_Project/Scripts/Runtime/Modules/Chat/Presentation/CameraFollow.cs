using UnityEngine;

namespace Nebula.Modules.Chat
{
    public class CameraFollow : MonoBehaviour
    {
        [SerializeField] private Transform target;
        [SerializeField] private Vector3 offset = new Vector3(0f, 3.2f, -6f);
        [SerializeField] private float followDamping = 8f;
        [SerializeField] private float lookHeight = 1.4f;
        [SerializeField] private bool followRotation;

        private void Start()
        {
            if (target == null) return;
            transform.position = DesiredPosition();
            transform.rotation = DesiredRotation();
        }

        private void LateUpdate()
        {
            if (target == null) return;

            float t = 1f - Mathf.Exp(-followDamping * Time.deltaTime);
            transform.position = Vector3.Lerp(transform.position, DesiredPosition(), t);
            transform.rotation = Quaternion.Slerp(transform.rotation, DesiredRotation(), t);
        }

        private Vector3 DesiredPosition()
        {
            Vector3 local = followRotation ? target.rotation * offset : offset;
            return target.position + local;
        }

        private Quaternion DesiredRotation()
        {
            Vector3 focus = target.position + Vector3.up * lookHeight;
            Vector3 dir = focus - transform.position;
            return dir.sqrMagnitude < 0.0001f ? transform.rotation : Quaternion.LookRotation(dir, Vector3.up);
        }
    }
}
