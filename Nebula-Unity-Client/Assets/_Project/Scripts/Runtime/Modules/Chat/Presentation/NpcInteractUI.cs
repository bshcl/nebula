using UnityEngine;
using UnityEngine.UI;

namespace Nebula.Modules.Chat
{
    public class NpcInteractUI : MonoBehaviour
    {
        [SerializeField] GameObject interactPrompt;
        [SerializeField] GameObject interactMenu;
        [SerializeField] ChatWindowUI chatWindow;
        [SerializeField] InventoryPanelUI inventoryPanel;
        [SerializeField] Button btnTalk;
        [SerializeField] Button btnBag;
        [SerializeField] Button btnQuest;

        bool _inRange = false;

        void OnEnable()
        {
            NpcInteractTrigger.OnPlayerInRange += HandleRange;
            if (btnTalk != null) btnTalk.onClick.AddListener(OnTalk);
            if (btnBag != null) btnBag.onClick.AddListener(OnBag);
            if (btnQuest != null) btnQuest.onClick.AddListener(OnQuest);
        }

        void OnDisable()
        {
            NpcInteractTrigger.OnPlayerInRange -= HandleRange;
            if (btnTalk != null) btnTalk.onClick.RemoveListener(OnTalk);
            if (btnBag != null) btnBag.onClick.RemoveListener(OnBag);
            if (btnQuest != null) btnQuest.onClick.RemoveListener(OnQuest);
        }

        void HandleRange(bool inRange)
        {
            _inRange = inRange;
            if (!inRange)
            {
                CloseAll();
                return;
            }

            if (interactPrompt != null) interactPrompt.SetActive(true);
        }

        void Update()
        {
            if (!_inRange) return;

            // Project Settings → Player → Active Input Handling
            if (Input.GetKeyDown(KeyCode.F))
            {
                chatWindow?.Hide();
                if (interactPrompt != null) interactPrompt.SetActive(false);
                if (interactMenu != null) interactMenu.SetActive(true);
            }

            if (Input.GetKeyDown(KeyCode.Escape))
                CloseAll();
        }

        void OnTalk()
        {
            if (interactMenu != null) interactMenu.SetActive(false);
            inventoryPanel?.Hide();
            chatWindow?.Show();
        }

        async void OnBag()
        {
            if (interactMenu != null) interactMenu.SetActive(false);
            chatWindow?.Hide();
            if (inventoryPanel != null)
                await inventoryPanel.RefreshAsync();
        }

        void OnQuest()
        {
            Debug.Log("[Interact] Quest claim placeholder");
        }

        void CloseAll()
        {
            if (interactPrompt != null) interactPrompt.SetActive(false);
            if (interactMenu != null) interactMenu.SetActive(false);
            chatWindow?.Hide();
            if (inventoryPanel != null)
                inventoryPanel.Hide();
        }
    }
}