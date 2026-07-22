using System.Threading.Tasks;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace Nebula.Modules.Chat
{
    public class InventoryPanelUI : MonoBehaviour
    {
        [SerializeField] private NebulaManager nebulaManager;
        [SerializeField] private GameObject panelRoot;
        [SerializeField] private TextMeshProUGUI itemsText;
        [SerializeField] private Button toggleButton;

        private void OnEnable()
        {
            if (nebulaManager != null)
                nebulaManager.OnGiftReceived += HandleGiftReceived;
            if (toggleButton != null)
                toggleButton.onClick.AddListener(OnToggleClicked);
        }

        private void OnDisable()
        {
            if (nebulaManager != null)
                nebulaManager.OnGiftReceived -= HandleGiftReceived;
            if (toggleButton != null)
                toggleButton.onClick.RemoveListener(OnToggleClicked);
        }

        // async void: required for event/button handlers that await.
        private async void HandleGiftReceived(string item) => await RefreshAsync();

        private async void OnToggleClicked() => await RefreshAsync();

        public async Task RefreshAsync()
        {
            if (nebulaManager == null || itemsText == null) return;

            var lines = await nebulaManager.FetchInventoryLinesAsync();
            itemsText.text = lines.Count == 0
                ? "(empty)"
                : string.Join("\n", lines);
            if (panelRoot != null) panelRoot.SetActive(true);
        }

        public void Hide()
        {
            if (panelRoot != null)
                panelRoot.SetActive(false);
        }
    }
}
