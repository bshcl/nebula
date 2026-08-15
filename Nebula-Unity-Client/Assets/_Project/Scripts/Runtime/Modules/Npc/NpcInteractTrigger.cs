using UnityEngine;

namespace Nebula.Modules.Npc
{
    public class NpcInteractTrigger : MonoBehaviour
    {
        public static event System.Action<bool> OnPlayerInRange;

        private void OnTriggerEnter(Collider other)
        {
            if (!other.CompareTag("Player")) return;
            Debug.Log("[Interact] enter");
            OnPlayerInRange?.Invoke(true);
        }

        private void OnTriggerExit(Collider other)
        {
            if (!other.CompareTag("Player")) return;
            Debug.Log("[Interact] exit");
            OnPlayerInRange?.Invoke(false);
        }
    }
}