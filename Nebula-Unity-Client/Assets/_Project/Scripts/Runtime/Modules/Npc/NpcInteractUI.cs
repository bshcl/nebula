using Nebula.Modules.Chat;
using Nebula.Modules.Inventory;
using Nebula.Modules.Player;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Nebula.Modules.Npc
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
        [SerializeField] private NebulaManager nebulaManager;
        [SerializeField] private SimplePlayerMove playerMove;

        private bool _inRange;

        private void SetPlayerLocked(bool locked)
        {
            if (playerMove != null)
                playerMove.SetLocked(locked);
        }

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
            SetPlayerLocked(false);
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
            if (!_inRange || Keyboard.current == null) return;

            if (Keyboard.current.fKey.wasPressedThisFrame)
                OpenMenu();

            if (Keyboard.current.escapeKey.wasPressedThisFrame)
                CloseAll();
        }

        private void OpenMenu()
        {
            if (chatWindow != null)
                chatWindow.Hide();
            if (interactPrompt != null)
                interactPrompt.SetActive(false);

            RefreshMenuButtons();

            if (interactMenu != null)
                interactMenu.SetActive(true);

            SetPlayerLocked(true);
        }

        private void RefreshMenuButtons()
        {
            bool hasSession = nebulaManager != null && nebulaManager.HasSession;
            Debug.Log($"[Interact] OpenMenu HasSession={hasSession}");

            if (btnBag != null)
                btnBag.gameObject.SetActive(hasSession);
            if (btnQuest != null)
                btnQuest.gameObject.SetActive(hasSession);
        }

        private void OnTalk()
        {
            SetPlayerLocked(true);

            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (inventoryPanel != null)
                inventoryPanel.Hide();

            // Session starts on Talk; then Bag / Quest become available.
            if (nebulaManager != null)
                nebulaManager.EnsureSession();
            RefreshMenuButtons();

            if (chatWindow != null)
                chatWindow.Show();
        }

        private async void OnBag()
        {
            SetPlayerLocked(true);

            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (chatWindow != null)
                chatWindow.Hide();
            if (inventoryPanel != null)
                await inventoryPanel.RefreshAsync();
        }

        private async void OnQuest()
        {
            SetPlayerLocked(true);

            if (interactMenu != null)
                interactMenu.SetActive(false);
            if (chatWindow != null)
                chatWindow.Hide();

            if (nebulaManager == null)
            {
                Debug.LogError("[Interact] NebulaManager not assigned");
                SetPlayerLocked(false);
                return;
            }

            var result = await nebulaManager.ClaimDefaultQuestAsync();
            Debug.Log($"[Interact] Quest claim result: {result}");

            if (inventoryPanel != null)
                await inventoryPanel.RefreshAsync();
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

            SetPlayerLocked(false);
        }
    }
}
