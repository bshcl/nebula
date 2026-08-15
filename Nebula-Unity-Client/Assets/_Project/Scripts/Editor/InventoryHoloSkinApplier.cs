using Nebula.Modules.Chat;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

namespace Nebula.Editor
{
    /// <summary>
    /// One-shot restyle: InventoryPanel → same holographic language as Chat / Interact.
    /// Menu: Nebula / UI / Apply Inventory Holo Skin
    /// </summary>
    public static class InventoryHoloSkinApplier
    {
        private const string HoloSpritePath =
            "Assets/_Project/Art/UI/Theme01/HoloPanelFrame.asset";

        private static readonly Color PanelTint = new Color(0.34f, 0.52f, 0.82f, 0.96f);
        private static readonly Color SlotTint = new Color(0.28f, 0.42f, 0.68f, 0.88f);
        private static readonly Color TopGlow = new Color(0.18f, 0.88f, 1f, 0.95f);
        private static readonly Color BottomGlow = new Color(0.43f, 0.3f, 1f, 0.72f);
        private static readonly Color LeftRail = new Color(0.25f, 0.78f, 1f, 0.9f);
        private static readonly Color TextIce = new Color(0.91f, 0.97f, 1f, 1f);

        [MenuItem("Nebula/UI/Apply Inventory Holo Skin")]
        public static void Apply()
        {
            var panel = FindInventoryPanel();
            if (panel == null)
            {
                EditorUtility.DisplayDialog(
                    "Inventory Holo Skin",
                    "Could not find InventoryPanel in the open scene(s).",
                    "OK");
                return;
            }

            var holo = LoadHoloSprite();
            if (holo == null)
            {
                EditorUtility.DisplayDialog(
                    "Inventory Holo Skin",
                    $"Missing holo sprite at:\n{HoloSpritePath}",
                    "OK");
                return;
            }

            Undo.RegisterFullObjectHierarchyUndo(panel, "Apply Inventory Holo Skin");

            StyleImage(panel.GetComponent<Image>(), holo, PanelTint);
            EnsureChrome(panel.transform, holo);
            StyleSlots(panel.transform, holo);
            StyleTexts(panel.transform);

            EditorSceneManager.MarkSceneDirty(panel.scene);
            Selection.activeGameObject = panel;
            Debug.Log("[Nebula] InventoryPanel holographic skin applied. Save the scene.");
        }

        private static GameObject FindInventoryPanel()
        {
            foreach (var root in Object.FindObjectsByType<Transform>(FindObjectsSortMode.None))
            {
                if (root.name == "InventoryPanel")
                    return root.gameObject;
            }

            return null;
        }

        private static Sprite LoadHoloSprite()
        {
            // Embedded Texture2D asset may expose multiple sprites; prefer 9-slice name.
            var all = AssetDatabase.LoadAllAssetsAtPath(HoloSpritePath);
            Sprite nineSlice = null;
            Sprite any = null;
            foreach (var obj in all)
            {
                if (obj is Sprite sprite)
                {
                    any = sprite;
                    if (sprite.name.Contains("9Slice") || sprite.name.Contains("Holo"))
                        nineSlice = sprite;
                }
            }

            return nineSlice != null ? nineSlice : any;
        }

        private static void StyleImage(Image image, Sprite sprite, Color tint)
        {
            if (image == null)
                return;

            image.sprite = sprite;
            image.type = Image.Type.Sliced;
            image.color = tint;
            image.pixelsPerUnitMultiplier = 1f;
        }

        private static void EnsureChrome(Transform panel, Sprite holo)
        {
            EnsureBar(panel, "Skin_TopGlow", TopGlow, new Vector2(0.5f, 1f), new Vector2(0.5f, 1f),
                new Vector2(0f, -8f), new Vector2(0f, -8f), new Vector2(1f, 6f));
            EnsureBar(panel, "Skin_BottomGlow", BottomGlow, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f),
                new Vector2(0f, 8f), new Vector2(0f, 8f), new Vector2(1f, 6f));
            EnsureBar(panel, "Skin_LeftRail", LeftRail, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f),
                new Vector2(6f, 0f), new Vector2(6f, 0f), new Vector2(4f, 0.92f));

            // Soft inner plate behind grid (optional dialogue-field feel)
            var field = EnsureChild(panel, "Skin_InnerField");
            var fieldImage = field.GetComponent<Image>() ?? field.AddComponent<Image>();
            StyleImage(fieldImage, holo, new Color(0.48f, 0.62f, 0.82f, 0.45f));
            var rt = field.GetComponent<RectTransform>();
            rt.anchorMin = new Vector2(0.06f, 0.08f);
            rt.anchorMax = new Vector2(0.94f, 0.88f);
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
            field.transform.SetSiblingIndex(0);
        }

        private static void EnsureBar(
            Transform parent,
            string name,
            Color color,
            Vector2 anchorMin,
            Vector2 anchorMax,
            Vector2 anchoredPos,
            Vector2 pivot,
            Vector2 sizeDelta)
        {
            var go = EnsureChild(parent, name);
            var image = go.GetComponent<Image>() ?? go.AddComponent<Image>();
            image.sprite = null;
            image.color = color;
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.pivot = pivot;
            rt.anchoredPosition = anchoredPos;
            // sizeDelta.x as width fraction when stretch? For glow bars use stretch + height.
            if (name.Contains("Rail"))
            {
                rt.anchorMin = new Vector2(0f, 0.08f);
                rt.anchorMax = new Vector2(0f, 0.92f);
                rt.pivot = new Vector2(0f, 0.5f);
                rt.anchoredPosition = new Vector2(8f, 0f);
                rt.sizeDelta = new Vector2(4f, 0f);
            }
            else if (name.Contains("Top"))
            {
                rt.anchorMin = new Vector2(0.08f, 1f);
                rt.anchorMax = new Vector2(0.92f, 1f);
                rt.pivot = new Vector2(0.5f, 1f);
                rt.anchoredPosition = new Vector2(0f, -10f);
                rt.sizeDelta = new Vector2(0f, 5f);
            }
            else
            {
                rt.anchorMin = new Vector2(0.08f, 0f);
                rt.anchorMax = new Vector2(0.92f, 0f);
                rt.pivot = new Vector2(0.5f, 0f);
                rt.anchoredPosition = new Vector2(0f, 10f);
                rt.sizeDelta = new Vector2(0f, 5f);
            }
        }

        private static GameObject EnsureChild(Transform parent, string name)
        {
            var existing = parent.Find(name);
            if (existing != null)
                return existing.gameObject;

            var go = new GameObject(name, typeof(RectTransform));
            Undo.RegisterCreatedObjectUndo(go, "Create " + name);
            go.transform.SetParent(parent, false);
            return go;
        }

        private static void StyleSlots(Transform panel, Sprite holo)
        {
            var template = panel.GetComponentInChildren<InventorySlotUI>(true);
            if (template == null)
                return;

            StyleImage(template.GetComponent<Image>(), holo, SlotTint);
            foreach (var tmp in template.GetComponentsInChildren<TextMeshProUGUI>(true))
                tmp.color = TextIce;
        }

        private static void StyleTexts(Transform panel)
        {
            foreach (var tmp in panel.GetComponentsInChildren<TextMeshProUGUI>(true))
            {
                // Don't force title-sized text; only ice tint.
                tmp.color = TextIce;
            }
        }
    }
}
