using System.Collections.Generic;
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
        [SerializeField] private Transform gridRoot;
        [SerializeField] private InventorySlotUI slotTemplate;
        [SerializeField] private int minimumSlotCount = 12;

        private void Awake()
        {
            EnsureRefs();

            // Grid mode: keep old ItemsText off so it cannot throw TMP wrap errors.
            if (gridRoot != null && slotTemplate != null && itemsText != null)
                itemsText.gameObject.SetActive(false);
        }

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

        // async void: Unity event/button handlers that await.
        private async void HandleGiftReceived(string item)
        {
            await RefreshAsync();
        }

        private async void OnToggleClicked()
        {
            await RefreshAsync();
        }

        public async Task RefreshAsync()
        {
            if (nebulaManager == null) return;

            EnsureRefs();
            var items = await nebulaManager.FetchInventoryItemsAsync();
            RenderInventory(items);

            if (panelRoot != null)
                panelRoot.SetActive(true);
        }

        public void Hide()
        {
            if (panelRoot != null)
                panelRoot.SetActive(false);
        }

        private void EnsureRefs()
        {
            if (panelRoot == null)
                panelRoot = gameObject;

            if (gridRoot == null)
            {
                var t = transform.Find("GridRoot");
                if (t != null)
                    gridRoot = t;
            }

            if (slotTemplate == null && gridRoot != null)
                slotTemplate = gridRoot.GetComponentInChildren<InventorySlotUI>(true);
        }

        private void RenderInventory(List<InventoryItemDto> items)
        {
            if (gridRoot != null && slotTemplate != null)
            {
                RenderGrid(items);
                if (itemsText != null)
                    itemsText.gameObject.SetActive(false);
                return;
            }

            if (itemsText == null) return;

            itemsText.gameObject.SetActive(true);
            itemsText.text = items.Count == 0
                ? "(empty)"
                : string.Join("\n", items.ConvertAll(item => $"{item.ItemId} x{item.Qty}"));
        }

        private void RenderGrid(List<InventoryItemDto> items)
        {
            ClearOldSlots();
            slotTemplate.gameObject.SetActive(false);

            int rendered = 0;
            foreach (var item in items)
            {
                var slot = CreateSlot();
                slot.SetData(item.ItemId, item.Qty);
                rendered++;
            }

            int total = Mathf.Max(minimumSlotCount, rendered);
            for (int i = rendered; i < total; i++)
            {
                var slot = CreateSlot();
                slot.SetEmpty();
            }
        }

        private InventorySlotUI CreateSlot()
        {
            var slot = Instantiate(slotTemplate, gridRoot);
            slot.gameObject.SetActive(true);
            return slot;
        }

        private void ClearOldSlots()
        {
            if (gridRoot == null) return;

            for (int i = gridRoot.childCount - 1; i >= 0; i--)
            {
                var child = gridRoot.GetChild(i);
                if (slotTemplate != null && child == slotTemplate.transform)
                    continue;

                Destroy(child.gameObject);
            }
        }
    }
}
