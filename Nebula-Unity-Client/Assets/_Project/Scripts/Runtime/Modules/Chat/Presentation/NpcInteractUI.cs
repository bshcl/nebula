using UnityEngine;
using UnityEngine.UI;

namespace Nebula.Modules.Chat
{
    /// <summary>
    /// F-key NPC menu: Talk / Bag / Quest. Subscribes to proximity events.
    /// Note: UnityEngine.Object must use explicit null checks, not ?.
    /// </summary>
    public class NpcInteractUI : MonoBehaviour
    {
        [SerializeField] private GameObject interactPrompt;
        [SerializeField] private GameObject interactMenu;
        [SerializeField] private ChatWindowUI chatWindow;
        [SerializeField] private InventoryPanelUI inventoryPanel;
        [SerializeField] private Button btnTalk;
        [SerializeField] private Button btnBag;
        [SerializeField] private Button btnQuest;

        private bool _inRange;

        private void OnEnable()
        {
            NpcInteractTrigger.OnPlayerInRange += HandleRange;
            if (btnTalk != null) btnTalk.onClick.AddListener(OnTalk);
            if (btnBag != null) btnBag.onClick.AddListener(OnBag);
            if (btnQuest != null) btnQuest.onClick.AddListener(OnQuest);
        }

        private void OnDisable()
        {
            NpcInteractTrigger.OnPlayerInRange -= HandleRange;
            if (btnTalk != null) btnTalk.onClick.RemoveListener(OnTalk);
            if (btnBag != null) btnBag.onClick.RemoveListener(OnBag);
            if (btnQuest != null) btnQuest.onClick.RemoveListener(OnQuest);
        }

        private void HandleRange(bool inRange)
        {
            _inRange = inRange;
            if (!inRange)
            {
                CloseAll();
                return;
            }

            if (interactPrompt != null)
                interactPrompt.SetActive(true);
        }

        private void Update()
        {
            if (!_inRange) return;

            // Requires Active Input Handling = Both (or Input Manager).
            if (Input.GetKeyDown(KeyCode.F))
                OpenMenu();

            if (Input.GetKeyDown(KeyCode.Escape))
                CloseAll();
        }

        private void OpenMenu()
        {
            if (chatWindow != null)
                chatWindow.Hide();
            if (interactPrompt != null)
                interactPrompt.SetActive(false);
            if (interactMenu != null)
                interactMenu.SetActive(true);
        }

        private void OnTalk()
        {
            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (inventoryPanel != null)
                inventoryPanel.Hide();
            if (chatWindow != null)
                chatWindow.Show();
        }

        private async void OnBag()
        {
            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (chatWindow != null)
                chatWindow.Hide();
            if (inventoryPanel != null)
                await inventoryPanel.RefreshAsync();
        }

        private void OnQuest()
        {
            Debug.Log("[Interact] Quest claim placeholder");
        }

        private void CloseAll()
        {
            if (interactPrompt != null)
                interactPrompt.SetActive(false);
            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (chatWindow != null)
                chatWindow.Hide();
            if (inventoryPanel != null)
                inventoryPanel.Hide();
        }
    }
}
