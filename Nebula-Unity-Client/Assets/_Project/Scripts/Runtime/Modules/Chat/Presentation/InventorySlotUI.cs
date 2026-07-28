using TMPro;
using UnityEngine;

namespace Nebula.Modules.Chat
{
    public class InventorySlotUI : MonoBehaviour
    {
        [SerializeField] private TextMeshProUGUI itemNameText;
        [SerializeField] private TextMeshProUGUI qtyText;

        private void Awake()
        {
            EnsureRefs();
            ConfigureTexts();
        }

        public void SetData(string itemId, int qty)
        {
            EnsureRefs();
            ConfigureTexts();

            if (itemNameText != null)
                itemNameText.text = string.IsNullOrWhiteSpace(itemId) ? "?" : itemId;

            if (qtyText != null)
                qtyText.text = qty > 0 ? $"x{qty}" : string.Empty;
        }

        public void SetEmpty()
        {
            EnsureRefs();
            ConfigureTexts();

            if (itemNameText != null)
                itemNameText.text = string.Empty;

            if (qtyText != null)
                qtyText.text = string.Empty;
        }

        private void EnsureRefs()
        {
            if (itemNameText == null)
            {
                var t = transform.Find("ItemNameText");
                if (t != null)
                    itemNameText = t.GetComponent<TextMeshProUGUI>();
            }

            if (qtyText == null)
            {
                var t = transform.Find("QtyText");
                if (t != null)
                    qtyText = t.GetComponent<TextMeshProUGUI>();
            }
        }

        /// <summary>
        /// Tiny slot rects + wrapping causes TMP "Line breaking recursion max threshold".
        /// Force single-line rendering for both labels.
        /// </summary>
        private void ConfigureTexts()
        {
            ConfigureSingleLine(itemNameText);
            ConfigureSingleLine(qtyText);
        }

        private static void ConfigureSingleLine(TextMeshProUGUI tmp)
        {
            if (tmp == null) return;

            tmp.textWrappingMode = TextWrappingModes.NoWrap;
            tmp.overflowMode = TextOverflowModes.Ellipsis;
            tmp.enableAutoSizing = false;
        }
    }
}
