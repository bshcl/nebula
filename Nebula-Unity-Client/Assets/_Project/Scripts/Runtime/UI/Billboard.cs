using UnityEngine;

namespace Nebula.UI
{
    /// <summary>
    /// Keeps this transform facing the main camera (typical world-space UI billboard).
    /// </summary>
    public class Billboard : MonoBehaviour
    {
        private void LateUpdate()
        {
            if (Camera.main == null) return;

            transform.LookAt(transform.position + Camera.main.transform.forward);
        }
    }
}
